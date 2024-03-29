from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Subscribe,
    Tag,
    TagRecipe
)
from users.models import User


class CommonSubscribed(metaclass=serializers.SerializerMetaclass):
    """
    Подписка пользователя на автора.
    """
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        """
        Обработка параметра is_subscribed подписок.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=request.user,
            following__id=obj.id
        ).exists()


class CommonRecipe(metaclass=serializers.SerializerMetaclass):
    """
    Класс для определения избранных
    рецептов и продуктов в корзине.
    """
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        """
        Обработка параметра is_favorited избранного.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user,
            recipe__id=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Обработка параметра is_in_shopping_cart в корзине.
        """
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Cart.objects.filter(
            user=request.user,
            recipe__id=obj.id
        ).exists()


class CommonCount(metaclass=serializers.SerializerMetaclass):
    """
    Класс для опредения количества рецептов автора.
    """
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        """
        Подсчет количества рецептов автора.
        """
        return Recipe.objects.filter(author__id=obj.id).count()


class RegistrationSerializer(UserCreateSerializer, CommonSubscribed):
    """
    Сериализатор модели пользователя.
    """
    class Meta:
        """
        Мета параметры сериализатора модели пользователя.
        """
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )
        write_only_fields = ('password',)
        read_only_fields = ('id',)
        extra_kwargs = {'is_subscribed': {'required': False}}

    def to_representation(self, obj):
        """
        Представление результатов сериализатора.
        """
        result = super(RegistrationSerializer, self).to_representation(obj)
        result.pop('password', None)
        return result


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели продуктов.
    """
    class Meta:
        """
        Мета параметры сериализатора модели продуктов.
        """
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        extra_kwargs = {
            'name': {'required': False},
            'measurement_unit': {'required': False}
        }


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели продуктов в рецепте для чтения.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        """
        Мета параметры сериализатора модели продуктов в рецепте.
        """
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор продуктов с количеством для записи.
    """
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        """
        Мета параметры сериализатора продуктов с количеством.
        """
        model = IngredientRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели тегов.
    """
    class Meta:
        """
        Мета параметры сериализатора модели тегов.
        """
        model = Tag
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': False},
            'slug': {'required': False},
            'color': {'required': False}
        }


class FavoriteSerializer(serializers.Serializer):
    """
    Сериализатор избранных рецептов.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class CartSerializer(serializers.Serializer):
    """
    Сериализатор корзины.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class RecipeSerializer(serializers.ModelSerializer, CommonRecipe):
    """
    Сериализатор модели рецептов.
    """
    author = RegistrationSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientrecipes',
        many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """
        Мета параметры сериализатора модели рецептов.
        """
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_in_shopping_cart',
            'is_favorited'
        )


class RecipeSerializerPost(serializers.ModelSerializer, CommonRecipe):
    """
    Сериализатор модели рецептов.
    """
    author = RegistrationSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountRecipeSerializer(
        source='ingredientrecipes',
        many=True
    )
    image = Base64ImageField(max_length=None, use_url=False,)

    class Meta:
        """
        Мета параметры сериализатора модели рецептов.
        """
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_in_shopping_cart',
            'is_favorited'
        )

    def validate_ingredients(self, value):
        """
        Валидация продуктов в рецепте.
        """
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть равным или больше 1!'
                )
            id_to_check = ingredient['ingredient']['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе!'
                )
            if ingredient_to_check in ingredients_list:
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте!'
                )
            ingredients_list.append(ingredient_to_check)
        return value

    def add_tags(self, tags_data, recipe):
        """
        Метод добавления тегов к рецепту.
        """
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
            recipe.save()
        return recipe

    def add_ingredients(self, ingredients, recipe):
        """
        Метод добавления ингредиетнов к рецепту.
        """
        for ingredient in ingredients:
            if not IngredientRecipe.objects.filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe
            ).exists():
                ingredientrecipe = IngredientRecipe.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe
                )
                ingredientrecipe.amount = ingredient['amount']
                ingredientrecipe.save()
            else:
                IngredientRecipe.objects.filter(
                    recipe=recipe
                ).delete()
                recipe.delete()
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте!'
                )
        return recipe

    def create(self, validated_data):
        """
        Метод создания рецептов.
        """
        author = validated_data.get('author')
        tags_data = validated_data.pop('tags')
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        ingredients = validated_data.pop('ingredientrecipes')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
        )
        recipe = self.add_tags(tags_data, recipe)
        recipe = self.add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Метод редактирования рецептов.
        """
        tags_data = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipes')
        TagRecipe.objects.filter(recipe=instance).delete()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        instance = self.add_tags(
            tags_data,
            instance
        )
        instance = self.add_ingredients(
            ingredients,
            instance
        )
        super().update(instance, validated_data)
        instance.save()
        return instance


class RecipeMinifieldSerializer(serializers.ModelSerializer):
    """
    Сериализатор для упрощенного отображения модели рецептов.
    """
    class Meta:
        """
        Мета параметры сериализатора упрощенного
        отображения модели рецептов.
        """
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(
    serializers.ModelSerializer,
    CommonSubscribed,
    CommonCount
):
    """
    Сериализатор для списка подписок.
    """
    recipes = serializers.SerializerMethodField()

    class Meta:
        """
        Мета параметры сериализатора списка подписок.
        """
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """
        Метод получения данных рецептов автора,
        в зависимости от параметра recipes_limit.
        """
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(
                author__id=obj.id
            ).order_by('id')[:recipes_limit]
        else:
            queryset = Recipe.objects.filter(author__id=obj.id).order_by('id')
        return RecipeMinifieldSerializer(queryset, many=True).data
