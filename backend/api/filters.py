from django_filters import rest_framework as django_filter
from rest_framework import filters

from recipes.models import Recipe, Tag
from users.models import User


class RecipeFilters(django_filter.FilterSet):
    """
    Настройка фильтров модели рецептов.
    """
    author = django_filter.ModelChoiceFilter(queryset=User.objects.all())
    tags = django_filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filter.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filter.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        """
        Параметры фильтров модели рецептов.
        """
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        """
        Метод обработки фильтров параметра is_favorited.
        """
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        """
        Метод обработки фильтров параметра is_in_shopping_cart.
        """
        if self.request.user.is_authenticated and value:
            return queryset.filter(carts__user=self.request.user)
        return queryset.all()


class IngredientSearchFilter(filters.SearchFilter):
    """
    Фильтр поиска модели продуктов.
    """
    search_param = 'name'
