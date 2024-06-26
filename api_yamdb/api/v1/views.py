from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Review, Title
from .filters import TitleFilterSet
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsModeratorIsAdminIsAuthorOrReadOnly)
from .serializers import (
    CategorySerializer, CommentSerializer, ConfirmationCodeSerializer,
    GenreSerializer, ReviewSerializer, TitleCreateSerializer, TitleSerializer,
    UserSignupSerializer, UserProfileSerializer)
from .viewsets import CreateListDestroyViewSet


User = get_user_model()


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).order_by('-year')
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilterSet
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TitleCreateSerializer
        return TitleSerializer


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsModeratorIsAdminIsAuthorOrReadOnly]
    http_method_names = ('get', 'post', 'patch', 'delete')

    def _get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self._get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self._get_title())


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsModeratorIsAdminIsAuthorOrReadOnly]
    http_method_names = ('get', 'post', 'patch', 'delete')

    def _get_review(self):
        return get_object_or_404(Review, id=self.kwargs.get('review_id'),
                                 title_id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self._get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self._get_review())


class SignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenView(APIView):
    def post(self, request):
        serializer = ConfirmationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data['username'])
        return Response({'token': str(
            AccessToken.for_user(user))
        }, status=status.HTTP_200_OK)


class UserProfileSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAdmin, )
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    http_method_names = ('get', 'post', 'patch', 'delete')

    @action(
        detail=False,
        url_path='me',
        methods=['GET', 'PATCH'],
        permission_classes=[IsAuthenticated]
    )
    def get_user_selfpage(self, request):
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
