import logging

import googlemaps
from django.conf import settings
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

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

logger = logging.getLogger(__name__)


class GMapViewSet(ViewSet):
    permission_classes = [IsAuthenticated, AppPermission]
    url_prefix = 'gmaps'
    api_basename = 'gmap_tools'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gmaps = googlemaps.Client(key=getattr(settings, 'GOOGLE_MAPS_API_KEY', ''))

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
        
        try:
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
            
            # Get detailed information for each place
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
                
                detailed_place = {
                    'place_id': place_id,
                    'name': result.get('name'),
                    'address': result.get('formatted_address'),
                    'location': result.get('geometry', {}).get('location', {'lat': 0, 'lng': 0}),
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
                    ]
                }
                detailed_places.append(detailed_place)
            
            response_data = {
                "status": "success",
                "places": detailed_places,
                "next_page_token": places_result.get('next_page_token')
            }
            
            output_serializer = LocationSearchOutputSerializer(response_data)
            return Response(output_serializer.data)
            
        except Exception as e:
            logger.error(f"Error in location search: {str(e)}")
            return Response(
                {"error": "An error occurred while searching for places"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        
        try:
            data = serializer.validated_data
            
            if data.get('address'):
                # Geocoding: address to coordinates
                action_type = "geocoding"
                map_data = {
                    "address": data['address'],
                    "components": data.get('components'),
                    "bounds": data.get('bounds'),
                    "region": data.get('region')
                }
                map_func = self.gmaps.geocode
                error_msg = "No results found for the provided address"
                
            else:
                # Reverse geocoding: coordinates to address
                action_type = "reverse_geocoding"
                map_data = {
                    "latlng": (data['lat'], data['lng']),
                    "result_type": data.get('result_type'),
                    "location_type": data.get('location_type')
                }
                map_func = self.gmaps.reverse_geocode
                error_msg = "No address found for the provided coordinates"

            map_result = map_func(**map_data)
            if not map_result:
                return Response(
                    {"error": error_msg},
                    status=status.HTTP_404_NOT_FOUND
                )

            results = self._format_geocoding_result(map_result)
            logger.info(f"{action_type} results: {results}")
            response_data = {
                "status": "success",
                "type": action_type,
                "results": results
            }
            
            output_serializer = GeocodingOutputSerializer(response_data)
            return Response(output_serializer.data)
                
        except Exception as e:
            raise e
            logger.error(f"Error in geocoding: {str(e)}")
            return Response(
                {"error": "An error occurred during geocoding"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        
        try:
            data = serializer.validated_data
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
            
            # Get detailed directions origin and destination
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

            # Format directions for better readability
            if directions_result:
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
                        'overview_polyline': route['overview_polyline'],
                        'warnings': route.get('warnings', []),
                        'waypoint_order': route.get('waypoint_order', []),
                        'steps': steps
                    }
                    formatted_directions.append(formatted_route)

                directions_result = formatted_directions
            
            response_data = {
                "status": "success",
                "distance_matrix": distance_matrix,
                "mode": data['mode']
            }
            
            if directions_result:
                response_data["directions"] = directions_result
            
            output_serializer = DistanceDirectionsOutputSerializer(response_data)
            return Response(output_serializer.data)
            
        except Exception as e:
            logger.error(f"Error in distance and directions: {str(e)}")
            return Response(
                {"error": "An error occurred while calculating distances and directions"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )