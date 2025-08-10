import logging
from urllib.parse import urlencode, quote

import googlemaps
import requests

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from requests.adapters import HTTPAdapter, Retry

from apps.app.permissions import AppPermission

from .serializers import (
    LocationSearchInputSerializer,
    LocationSearchOutputSerializer,
    GeocodingInputSerializer,
    GeocodingOutputSerializer,
    DistanceDirectionsInputSerializer,
    DistanceDirectionsOutputSerializer,
    ErrorSerializer
)
from .enums import (
    GeoCodingAction,
    EmbedUrlType,
)
from.exceptions import GMapUnexpectedError, QuotaExceededError

logger = logging.getLogger(__name__)

EMBED_URL_TYPES = (EmbedUrlType.place.value, EmbedUrlType.direction.value)

GMAP_RETRY = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=googlemaps.client._RETRIABLE_STATUSES
)
GMAP_CUSTOM_ADAPTER = HTTPAdapter(max_retries=GMAP_RETRY)

API_EXCEPTIONS = (
    googlemaps.exceptions.HTTPError,
    googlemaps.exceptions.ApiError,
)

BASE_EMBED_URL = "https://www.google.com/maps/embed/v1/"

class GMapViewSet(ViewSet):
    permission_classes = [IsAuthenticated, AppPermission]
    url_prefix = 'gmaps'
    api_basename = 'gmap_tools'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gmaps = googlemaps.Client(
            key=getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
            retry_over_query_limit=False,
        )
        self.gmaps.session.mount('https://', GMAP_CUSTOM_ADAPTER)

    @staticmethod
    def raise_on_invalid_map_status(
        map_status: str,
        error_message: str | None = None,
    ):
        if not map_status or map_status in ("OK", "ZERO_RESULTS"):
            return

        exception_class = None
        if "LIMIT" in map_status:
            exception_class = QuotaExceededError
        else:
            exception_class = GMapUnexpectedError

        # Raise exception for send issue to logs with error message
        if error_message:
            raise exception_class(error_message)

        raise exception_class

    def generate_google_map_link(self, embed_type: EmbedUrlType, **kwargs):
        if embed_type == EmbedUrlType.place:
            return f"https://www.google.com/maps/search/?api=1&query={kwargs.get('query')}"
        elif embed_type == EmbedUrlType.direction:
            return (
                f"https://www.google.com/maps/dir/?api=1&origin={kwargs.get('origin')}"
                f"&destination={kwargs.get('destination')}&travelmode={kwargs.get('mode')}"
            )

    @extend_schema(
        request=LocationSearchInputSerializer,
        responses={
            200: LocationSearchOutputSerializer,
            400: ErrorSerializer,
            500: ErrorSerializer
        },
        description="Search for places near a specific location with customizable radius and filters. "
                   "Get detailed place information including ratings, opening hours, and contact details.",
        summary="Search nearby places",
        tags=["Google Map Tools"],
    )
    @action(detail=False, methods=["post"])
    def location(self, request):
        """
        Features:
        - Search for places near a specific location with customizable radius and filters
        - Get detailed place information including ratings, opening hours, and contact details
        """
        serializer = LocationSearchInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

        data = serializer.validated_data
            
        # Get location coordinates
        if data.get('lat') and data.get('lng'):
            location = {'lat': data['lat'], 'lng': data['lng']}
        else:
            location = data['location']
            # Convert location to lat/lng if it's an address
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return Response(
                    {"error": "Could not geocode the provided location"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            location = geocode_result[0]['geometry']['location']

        # Search for nearby places
        try:
            places_result = self.gmaps.places_nearby(
                location=location,
                radius=data['radius'],
                type=data.get('type'),
                keyword=data.get('keyword'),
                name=data.get('name'),
                min_price=data.get('min_price'),
                max_price=data.get('max_price'),
                open_now=data.get('open_now')
            )
        except API_EXCEPTIONS:
            places_result = {}

        api_status = places_result.get('status')
        self.raise_on_invalid_map_status(
            api_status,
            f"Error searching for nearby places ({api_status})"
        )
            
        # on OK status, Get detailed information for each place
        detailed_places = []
        for place in places_result.get('results', []):
            place_id = place['place_id']
                
            # Get place details
            place_details = self.gmaps.place(
                place_id=place_id,
                fields=[
                    'name', 'rating', 'formatted_phone_number', 'website',
                    'opening_hours', 'geometry', 'formatted_address',
                    'price_level', 'user_ratings_total', 'reviews'
                ]
            )
                
            result = place_details.get('result', {})
            opening_hours = result.get('opening_hours', {})

            location = result.get('geometry', {}).get('location', {})
            detailed_place = {
                'place_id': place_id,
                'name': result.get('name'),
                'address': result.get('formatted_address'),
                'location': location,
                'rating': result.get('rating'),
                'user_ratings_total': result.get('user_ratings_total'),
                'price_level': result.get('price_level'),
                'phone_number': result.get('formatted_phone_number'),
                'website': result.get('website'),
                'opening_hours': opening_hours.get('weekday_text'),
                'is_open_now': opening_hours.get('open_now'),
                'reviews': [
                    {
                        'author_name': review.get('author_name', ''),
                        'rating': review.get('rating', 0),
                        'text': review.get('text', ''),
                        'time': review.get('time', 0)
                    }
                    for review in result.get('reviews', [])[:3]
                ],
                "url": self.generate_google_map_link(
                    EmbedUrlType.place,
                    query=quote(result.get('name', '')),
                )
            }
            detailed_places.append(detailed_place)
            
        response_data = {
            "results": detailed_places,
        }

        output_serializer = LocationSearchOutputSerializer(response_data)
        return Response(output_serializer.data)

    @staticmethod
    def _format_geocoding_result(results: dict):
        """Helper method to format geocoding results"""
        formatted_results = []
        for result in results:
            formatted_result = {
                'formatted_address': result['formatted_address'],
                'address_components': result['address_components'],
                'types': result['types'],
                'place_id': result['place_id']
            }

            if geometry := result.get('geometry'):
                formatted_result['geometry'] = {
                    'location': geometry['location'],
                    'location_type': geometry['location_type'],
                    'bounds': geometry.get('bounds'),
                    'viewport': geometry['viewport']
                }

            formatted_results.append(formatted_result)

        return formatted_results

    @extend_schema(
        request=GeocodingInputSerializer,
        responses={
            200: GeocodingOutputSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
            500: ErrorSerializer
        },
        description="Convert addresses to coordinates (geocoding) or coordinates to addresses (reverse geocoding). "
                   "Supports component filtering, bounds biasing, and region preferences.",
        summary="Geocoding and reverse geocoding",
        tags=["Google Map Tools"],
    )
    @action(detail=False, methods=["post"])
    def geocoding(self, request):
        """
        Features:
        - Convert addresses to coordinates (geocoding)
        - Convert coordinates to addresses (reverse geocoding)
        """
        serializer = GeocodingInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
            
        if data.get('address'):
            # Geocoding: address to coordinates
            action_type = GeoCodingAction.GEOCODING
            map_data = {
                "address": data['address'],
                "components": data.get('components'),
                "bounds": data.get('bounds'),
                "region": data.get('region')
            }
            map_func = self.gmaps.geocode
                
        else:
            # Reverse geocoding: coordinates to address
            action_type = GeoCodingAction.REVERSE_GEOCODING
            map_data = {
                "latlng": (data['lat'], data['lng']),
                "result_type": data.get('result_type'),
                "location_type": data.get('location_type')
            }
            map_func = self.gmaps.reverse_geocode

        try:
            map_result = map_func(**map_data)
        except API_EXCEPTIONS:
            map_result = []

        results = self._format_geocoding_result(map_result)
        response_data = {
            "type": action_type,
            "results": results
        }

        output_serializer = GeocodingOutputSerializer(response_data)
        return Response(output_serializer.data)

    @extend_schema(
        request=DistanceDirectionsInputSerializer,
        responses={
            200: DistanceDirectionsOutputSerializer,
            400: ErrorSerializer,
            500: ErrorSerializer
        },
        description="Calculate distances and travel times between single origin and destination. "
                   "Get detailed turn-by-turn directions between points with support for different travel modes.",
        summary="Distance matrix and directions",
        tags=["Google Map Tools"],
    )
    @action(detail=False, methods=["post"])
    def distance_and_directions(self, request):
        """
        Features:
        - Calculate distance and travel times between single origin and destination
        - Get detailed turn-by-turn directions between two points
        - Support for different travel modes (driving, walking, bicycling, transit)
        """
        serializer = DistanceDirectionsInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        

        data = serializer.validated_data
        distance_matrix = None
        # Get detailed directions origin and destination
        try:
            directions_result = self.gmaps.directions(
                origin=data['origins'],
                destination=data['destinations'],
                mode=data['mode'],
                waypoints=data.get('waypoints'),
                optimize_waypoints=data['optimize_waypoints'],
                avoid=data.get('avoid'),
                departure_time=data.get('departure_time'),
                arrival_time=data.get('arrival_time'),
                alternatives=data['alternatives'],
            )
        except API_EXCEPTIONS:
            directions_result = []

        response_data = {}
        # Format directions for better readability
        if directions_result:
            # Get distance matrix
            distance_matrix = self.gmaps.distance_matrix(
                origins=data['origins'],
                destinations=data['destinations'],
                mode=data['mode'],
                units=data['units'],
                avoid=data.get('avoid'),
                departure_time=data.get('departure_time'),
                arrival_time=data.get('arrival_time'),
            )
            # on directions exists and failed distance matrix, only log error message
            try:
                self.raise_on_invalid_map_status(
                    distance_matrix['status'],
                    f"Error calculating distance matrix ({distance_matrix['status']})"
                )
            except (QuotaExceededError, GMapUnexpectedError) as e:
                if isinstance(e, GMapUnexpectedError):
                    logger.error(f"Distance matrix failed unexpectedly ({distance_matrix['status']})")

            if distance_matrix.get("status") != "OK":
                distance_matrix = None

            formatted_directions = []
            for route in directions_result:
                steps = []
                for leg in route['legs']:
                    for step in leg['steps']:
                        formatted_step = {
                            'instruction': step['html_instructions'],
                            'distance': step['distance'],
                            'duration': step['duration'],
                            'start_location': step['start_location'],
                            'end_location': step['end_location'],
                            'maneuver': step.get('maneuver'),
                            'travel_mode': step['travel_mode']
                        }
                        steps.append(formatted_step)

                overview_polyline = route.get('overview_polyline')
                overview_polyline.pop('points', None)
                formatted_route = {
                    'summary': route['summary'],
                    'legs': [{
                        'distance': leg['distance'],
                        'duration': leg['duration'],
                        'start_address': leg['start_address'],
                        'end_address': leg['end_address'],
                        'start_location': leg['start_location'],
                        'end_location': leg['end_location']
                    } for leg in route['legs']],
                    'overview_polyline': overview_polyline,
                    'warnings': route.get('warnings', []),
                    'waypoint_order': route.get('waypoint_order', []),
                    'steps': steps
                }
                formatted_directions.append(formatted_route)

            directions_result = formatted_directions
            
            response_data.update({
                "mode": data['mode'],
                "directions": directions_result,
                "distance_matrix": distance_matrix,
                "url": self.generate_google_map_link(
                    EmbedUrlType.direction,
                    origin=quote(data['origins']),
                    destination=quote(data['destinations']),
                    mode=data.get('mode')
                )
            })

        output_serializer = DistanceDirectionsOutputSerializer({"results": response_data})
        return Response(output_serializer.data)
