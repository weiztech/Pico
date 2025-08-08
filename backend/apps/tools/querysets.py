from django.db import models


class ToolQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            is_active=True,
            display=True,
            category__display=True
        )


class ToolCategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(display=True)
