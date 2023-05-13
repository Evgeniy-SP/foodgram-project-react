from http import HTTPStatus

from django.db.models import Sum
from django.shortcuts import get_list_or_404, get_object_or_404
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Subscribe,
    Tag
)
from users.models import User
from .utils import canvas_method
from .filters import IngredientSearchFilter, RecipeFilters
from .serializers import (
    CartSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeSerializerPost,
    RegistrationSerializer,
    SubscriptionSerializer,
    TagSerializer
)


class CreateUserView(UserViewSet):
    """
    Обработка моделей пользователя.
    """
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class SubscribeViewSet(viewsets.ModelViewSet):
    """
    Обработка моделей подписок.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_list_or_404(User, following__user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Метод создания подписки.
        """
        user_id = self.kwargs.get('users_id')
        user = get_object_or_404(User, id=user_id)
        Subscribe.objects.create(user=request.user, following=user)
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        """
        Метод удаления подписок.
        """
        author_id = self.kwargs['users_id']
        user_id = request.user.id
        subscribe = get_object_or_404(
            Subscribe, user__id=user_id,
            following__id=author_id
        )
        subscribe.delete()
        return Response(HTTPStatus.NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Обработка моделей тэгов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Обработка моделей рецептов.
    """
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_class = RecipeFilters
    filter_backends = [DjangoFilterBackend, ]

    def perform_create(self, serializer):
        """
        Подстановка параметров автора при создании рецепта.
        """
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """
        Выбора сериализатора в зависимости от запроса.
        """
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeSerializerPost


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Обработка модели продуктов.
    """
    queryset = Ingredient.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, IngredientSearchFilter)
    pagination_class = None
    search_fields = ['^name', ]


class BaseFavoriteCartViewSet(viewsets.ModelViewSet):
    """
    Базовый вьюсет обработки модели корзины и избранных рецептов.
    """
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Создание модели корзины или избранных рецептов.
        """
        recipe_id = int(self.kwargs['recipes_id'])
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(user=request.user, recipe=recipe)
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        """
        Удаление объектов модели корзины или избранных рецептов.
        """
        recipe_id = self.kwargs['recipes_id']
        user_id = request.user.id
        object = get_object_or_404(
            self.model,
            user__id=user_id,
            recipe__id=recipe_id
        )
        object.delete()
        return Response(HTTPStatus.NO_CONTENT)


class CartViewSet(BaseFavoriteCartViewSet):
    """
    Обработка модели корзины.
    """
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    model = Cart


class FavoriteViewSet(BaseFavoriteCartViewSet):
    """
    Обработка модели избранных рецептов.
    """
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    model = Favorite


class DownloadCart(viewsets.ModelViewSet):
    """
    Сохранение файла списка покупок.
    """
    permission_classes = [permissions.IsAuthenticated]

    def download(self, request):
        """
        Создания списка покупок.
        """
        result = IngredientRecipe.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(ingredient_total=Sum('amount'))
        return canvas_method(result)
