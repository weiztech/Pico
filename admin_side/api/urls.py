from django.urls import path
import admin_side.api.scraper_monitor.views as SCRAPER_MONITOR

urlpatterns = [
    path("scraper_reports/", SCRAPER_MONITOR.ScraperReportsListAPIView.as_view(), name="scraper-report-api-list"),
] 