from rest_framework import serializers


from .enums import GeoCodingAction


class LocationInputSerializer(serializers.Serializer):
    """Serializer for location coordinates"""
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class LocationSearchInputSerializer(serializers.Serializer):
    """Input serializer for location search endpoint"""
    location = serializers.CharField(
        help_text="Location as address string or use lat/lng fields for coordinates",
        required=False
    )
    lat = serializers.FloatField(required=False, help_text="Latitude (alternative to location string)")
    lng = serializers.FloatField(required=False, help_text="Longitude (alternative to location string)")
    radius = serializers.IntegerField(
        default=1500, 
        min_value=1, 
        max_value=50000,
        help_text="Search radius in meters (max 50km)"
    )
    type = serializers.CharField(
        required=False,
        help_text="Place type (e.g., restaurant, gas_station, hospital)"
    )
    keyword = serializers.CharField(
        required=False,
        help_text="Search keyword to match against place names (e.g., place to relax, best coffee shop)"
    )
    name = serializers.CharField(
        required=False,
        help_text="Specific place name to search for"
    )
    min_price = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        help_text="Minimum price level (0-4, where 0 is free and 4 is very expensive)"
    )
    max_price = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=4,
        help_text="Maximum price level (0-4, where 0 is free and 4 is very expensive)"
    )
    open_now = serializers.BooleanField(
        required=False,
        help_text="Filter places that are open now"
    )

    def validate(self, data):
        """Ensure either location string or lat/lng coordinates are provided"""
        location = data.get('location')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not location and (lat is None or lng is None):
            raise serializers.ValidationError(
                "Either 'location' string or both 'lat' and 'lng' coordinates must be provided"
            )
        
        return data


class ReviewSerializer(serializers.Serializer):
    """Serializer for place reviews"""
    author_name = serializers.CharField()
    rating = serializers.IntegerField()
    text = serializers.CharField()
    time = serializers.IntegerField()


class PlaceDetailSerializer(serializers.Serializer):
    """Serializer for detailed place information"""
    place_id = serializers.CharField()
    name = serializers.CharField()
    address = serializers.CharField(allow_null=True)
    location = LocationInputSerializer()
    rating = serializers.FloatField(allow_null=True)
    user_ratings_total = serializers.IntegerField(allow_null=True)
    price_level = serializers.IntegerField(allow_null=True)
    phone_number = serializers.CharField(allow_null=True)
    website = serializers.URLField(allow_null=True)
    opening_hours = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        help_text="Array of opening hours for each day of the week"
    )
    is_open_now = serializers.BooleanField(allow_null=True)
    reviews = ReviewSerializer(many=True, required=False)
    url = serializers.URLField(required=False)


class LocationSearchOutputSerializer(serializers.Serializer):
    """Output serializer for location search endpoint"""
    results = PlaceDetailSerializer(many=True)


class GeocodingInputSerializer(serializers.Serializer):
    """Input serializer for geocoding endpoint"""
    address = serializers.CharField(
        required=False,
        help_text="Address to geocode (for forward geocoding)"
    )
    lat = serializers.FloatField(
        required=False,
        help_text="Latitude (for reverse geocoding)"
    )
    lng = serializers.FloatField(
        required=False,
        help_text="Longitude (for reverse geocoding)"
    )
    components = serializers.DictField(
        required=False,
        help_text="Component filters (e.g., {'country': 'US', 'postal_code': '12345'})"
    )
    bounds = serializers.DictField(
        required=False,
        help_text=(
            "Bounding box to bias results "
            "(e.g., {'northeast': {'lat': 40.714224, 'lng': -73.961452}, "
            "'southwest': {'lat': 40.626481, 'lng': -74.053177}})"
        )
    )
    region = serializers.CharField(
        required=False,
        help_text="Region code to bias results"
    )
    result_type = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=(
            "Filter results by type (for reverse geocoding) "
            "(e.g., street_address, route, geocode, country, locality, postal_code, administrative_area_level_1, )"
        )
    )
    location_type = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=(
            "Filter results by location type (for reverse geocoding) "
            "(e.g., rooftop, range_interpolated, geometric_center", "approximate)"
        )
    )

    def validate(self, data):
        """Ensure either address or lat/lng coordinates are provided"""
        address = data.get('address')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not address and (lat is None or lng is None):
            raise serializers.ValidationError(
                "Either 'address' or both 'lat' and 'lng' parameters are required"
            )
        
        return data


class BoundsSerializer(serializers.Serializer):
    """Serializer for geometric bounds"""
    northeast = LocationInputSerializer()
    southwest = LocationInputSerializer()


class GeometrySerializer(serializers.Serializer):
    """Serializer for geometry information"""
    location = LocationInputSerializer()
    location_type = serializers.CharField()
    bounds = BoundsSerializer(required=False, allow_null=True)
    viewport = BoundsSerializer()


class AddressComponentSerializer(serializers.Serializer):
    """Serializer for address components"""
    long_name = serializers.CharField()
    short_name = serializers.CharField()
    types = serializers.ListField(child=serializers.CharField())


class GeocodeResultSerializer(serializers.Serializer):
    """Serializer for individual geocoding result"""
    formatted_address = serializers.CharField()
    geometry = GeometrySerializer(required=False)
    address_components = AddressComponentSerializer(many=True, required=False)
    types = serializers.ListField(child=serializers.CharField())
    place_id = serializers.CharField()


class GeocodingOutputSerializer(serializers.Serializer):
    """Output serializer for geocoding endpoint"""
    type = serializers.ChoiceField(choices=GeoCodingAction.choices())
    results = GeocodeResultSerializer(many=True)


class DistanceDirectionsInputSerializer(serializers.Serializer):
    """Input serializer for distance and directions endpoint"""
    TRAVEL_MODES = [
        ('driving', 'Driving'),
        ('walking', 'Walking'),
        ('bicycling', 'Bicycling'),
        ('transit', 'Transit'),
    ]
    
    UNITS = [
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    ]
    
    AVOID_OPTIONS = [
        ('tolls', 'Tolls'),
        ('highways', 'Highways'),
        ('ferries', 'Ferries'),
        ('indoor', 'Indoor'),
    ]
    
    TRAFFIC_MODELS = [
        ('best_guess', 'Best Guess'),
        ('pessimistic', 'Pessimistic'),
        ('optimistic', 'Optimistic'),
    ]

    origins = serializers.CharField(
        help_text="Origin address or coordinate"
    )
    destinations = serializers.CharField(
        help_text="Destination address or coordinate"
    )
    mode = serializers.ChoiceField(
        choices=TRAVEL_MODES,
        default='driving',
        help_text="Travel mode"
    )
    units = serializers.ChoiceField(
        choices=UNITS,
        default='metric',
        help_text="Unit system"
    )
    avoid = serializers.ListField(
        child=serializers.ChoiceField(choices=AVOID_OPTIONS),
        required=False,
        help_text="Route restrictions to avoid"
    )
    waypoints = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Waypoints for directions (only used with single origin/destination)"
    )
    optimize_waypoints = serializers.BooleanField(
        default=False,
        help_text="Optimize waypoint order"
    )
    alternatives = serializers.BooleanField(
        default=False,
        help_text="Return alternative routes"
    )
    departure_time = serializers.IntegerField(
        required=False,
        help_text="Departure time as Unix timestamp"
    )
    arrival_time = serializers.IntegerField(
        required=False,
        help_text="Arrival time as Unix timestamp"
    )
    # traffic_model = serializers.ChoiceField(
    #    choices=TRAFFIC_MODELS,
    #    default='best_guess',
    #    help_text="Traffic model for predictions"
    # )


class DistanceDurationSerializer(serializers.Serializer):
    """Serializer for distance and duration values"""
    text = serializers.CharField()
    value = serializers.IntegerField()


class DistanceMatrixElementSerializer(serializers.Serializer):
    """Serializer for distance matrix elements"""
    distance = DistanceDurationSerializer(required=False)
    duration = DistanceDurationSerializer(required=False)
    duration_in_traffic = DistanceDurationSerializer(required=False)
    status = serializers.CharField()


class DistanceMatrixRowSerializer(serializers.Serializer):
    """Serializer for distance matrix rows"""
    elements = DistanceMatrixElementSerializer(many=True)


class DistanceMatrixSerializer(serializers.Serializer):
    """Serializer for distance matrix response"""
    destination_addresses = serializers.ListField(child=serializers.CharField())
    origin_addresses = serializers.ListField(child=serializers.CharField())
    rows = DistanceMatrixRowSerializer(many=True)
    status = serializers.CharField()


class DirectionStepSerializer(serializers.Serializer):
    """Serializer for individual direction step"""
    instruction = serializers.CharField()
    distance = DistanceDurationSerializer()
    duration = DistanceDurationSerializer()
    start_location = LocationInputSerializer()
    end_location = LocationInputSerializer()
    maneuver = serializers.CharField(allow_null=True)
    travel_mode = serializers.CharField()


class RouteLegSerializer(serializers.Serializer):
    """Serializer for route legs"""
    distance = DistanceDurationSerializer()
    duration = DistanceDurationSerializer()
    start_address = serializers.CharField()
    end_address = serializers.CharField()
    start_location = LocationInputSerializer()
    end_location = LocationInputSerializer()


class DirectionRouteSerializer(serializers.Serializer):
    """Serializer for direction routes"""
    summary = serializers.CharField()
    legs = RouteLegSerializer(many=True)
    overview_polyline = serializers.DictField()
    warnings = serializers.ListField(child=serializers.CharField())
    waypoint_order = serializers.ListField(child=serializers.IntegerField())
    steps = DirectionStepSerializer(many=True)


class DistanceDirectionsSerializer(serializers.Serializer):
    """Output serializer for directions endpoint"""
    distance_matrix = DistanceMatrixSerializer(required=False)
    mode = serializers.CharField(required=False)
    directions = DirectionRouteSerializer(many=True, required=False)
    url = serializers.URLField(required=False)


class DistanceDirectionsOutputSerializer(serializers.Serializer):
    """Output serializer for distance and directions endpoint"""
    results = DistanceDirectionsSerializer(required=False)


class ErrorSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField()
