from rest_framework.decorators import action 
from rest_framework import viewsets, permissions, status, serializers 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpResponse
from .models import Cliente, Ordem, Compartilhamento, FavoritasCliente, FavoritasOrdem, Comentario, Anexo
from .serializers import (UserSerializer, ClienteSerializer, OrdemSerializer, LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer, CompartilhamentoSerializer, FavoritasClienteSerializer, FavoritasOrdemSerializer, ComentarioSerializer, AnexoSerializer)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login as django_login
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from django.http import FileResponse
from fpdf import FPDF

NOTIFICACOES = {}
UserModel = get_user_model()

@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de cadastro com os dados:", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print("Cadastro realizado com sucesso para o usuário:", user.username)
            return Response({"user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        print("Falha no cadastro com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de login com os dados:", request.data)
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            django_login(request, user)
            print("Login realizado com sucesso para o usuário:", user.username)

            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'id': user.id
            })
        print("Falha no login com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de logout")
        auth_logout(request)
        print("Logout realizado com sucesso")
        return Response({"detail": _("Deslogado com sucesso.")}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de reset de senha com os dados:", request.data)
        serializer = PasswordResetSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                print("Solicitação de reset de senha realizada com sucesso")
                return Response({"detail": "Solicitação de reset de senha realizada com sucesso."}, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"Erro ao processar reset de senha: {e}")
                return Response({"detail": f"Erro ao processar reset de senha: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print("Falha na solicitação de reset de senha com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de confirmação de reset de senha com os dados:", request.data)
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print("Confirmação de reset de senha realizada com sucesso")
            return Response({"detail": _("Reset de senha realizado com sucesso.")}, status=status.HTTP_200_OK)
        print("Falha na confirmação de reset de senha com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("Recebida solicitação de alteração de senha com os dados:", request.data)
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print("Alteração de senha realizada com sucesso")
            return Response({"detail": _("Senha alterada com sucesso.")}, status=status.HTTP_200_OK)
        print("Falha na alteração de senha com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = DjangoUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        search_query = self.request.query_params.get('search', None)
        print(f"[BACKEND] Buscando dados de usuários com o critério de busca: {search_query}")

        try:
            if search_query:
                queryset = DjangoUser.objects.filter(
                    Q(username__icontains=search_query) |
                    Q(email__icontains=search_query)
                )
            else:
                queryset = DjangoUser.objects.filter(id=user.id)

            if queryset.exists():
                print(f"[BACKEND] Usuários encontrados: {[f'ID={u.id}, Nome={u.username}' for u in queryset]}")
            else:
                print(f"[BACKEND] Nenhum usuário encontrado para o critério de busca: {search_query}")
            return queryset
        except Exception as e:
            print(f"[BACKEND] Erro ao buscar usuários: {e}")
            import traceback
            traceback.print_exc()
            return DjangoUser.objects.none()  # Retorna um queryset vazio em caso de erro

        

class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Cliente.objects.filter(user=user).order_by('id')
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(nome__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            print(f"Erro ao recuperar o cliente: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class OrdemViewSet(viewsets.ModelViewSet):
    serializer_class = OrdemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Ordem.objects.filter(Q(user=user) | Q(compartilhamento__usuario_destino=user)).distinct()

        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(descricao__icontains=search_query) |
                Q(cliente__nome__icontains=search_query) |
                Q(hardware__icontains=search_query) |
                Q(servico__icontains=search_query) |
                Q(compartilhamento__usuario_destino__username__icontains=search_query) |
                Q(anexo__arquivo__icontains=search_query) |
                Q(comentario__texto__icontains=search_query)
            )

        return queryset

    def perform_create(self, serializer):
        print("OrdemViewSet perform_create chamado com dados:", serializer.validated_data)
        try:
            serializer.save(user=self.request.user)
            print("Ordem criada com sucesso pelo usuário:", self.request.user.username)
        except Exception as e:
            print(f"Erro ao criar a ordem: {e}")
            raise

    def create(self, request, *args, **kwargs):
        print(f"Recebida solicitação de criação de ordem com os dados: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                print(f"Erro durante a criação da ordem: {e}")
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("Falha na validação com erros:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        print(f"OrdemViewSet update chamado com dados: {request.data}")
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                self.perform_update(serializer)
                print("Ordem atualizada com sucesso:", instance.id)
                return Response(serializer.data)
            except Exception as e:
                print(f"Erro ao atualizar a ordem: {e}")
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print("Falha na validação de atualização de ordem com os erros:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        print(f"OrdemViewSet destroy chamado para id: {kwargs.get('pk')}")
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            print("Ordem deletada com sucesso:", instance.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"Erro ao deletar a ordem: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        print(f"OrdemViewSet retrieve chamado para id: {kwargs.get('pk')}")
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            print(f"Erro ao recuperar a ordem: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FavoritasOrdemViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritasOrdemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = FavoritasOrdem.objects.filter(usuario=user)
        print(f"FavoritasOrdemViewSet.get_queryset: {queryset}")
        return queryset

    def create(self, request, *args, **kwargs):
        print(f"FavoritasOrdemViewSet.create: dados recebidos {request.data}")
        data = request.data.copy()
        data['usuario'] = request.user.id

        # Verifica se a ordem já está favoritada pelo usuário atual
        if FavoritasOrdem.objects.filter(usuario=request.user, ordem=data['ordem']).exists():
            print("Erro: A ordem já está favoritada.")
            return Response({"detail": "A ordem já está favoritada."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                print(f"FavoritasOrdemViewSet.create: favorito criado com sucesso {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                print(f"Erro ao criar favorito: {e}")
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"FavoritasOrdemViewSet.create: erros de validação {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            print(f"FavoritasOrdemViewSet.destroy: dados recebidos para deletar {kwargs}")
            # Usa o ID do favorito diretamente ao invés de procurar pela ordem
            instance = FavoritasOrdem.objects.get(id=kwargs['pk'], usuario=request.user)
            print(f"FavoritasOrdemViewSet.destroy: tentando deletar favorito {instance}")
            self.perform_destroy(instance)
            print(f"FavoritasOrdemViewSet.destroy: favorito deletado com sucesso")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FavoritasOrdem.DoesNotExist:
            print("Erro: Favorito não encontrado")
            return Response({"detail": "Favorito não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Erro ao deletar favorito: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# A lógica para FavoritasClienteViewSet permanece a mesma
class FavoritasClienteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritasClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = FavoritasCliente.objects.filter(usuario=user)
        print(f"FavoritasClienteViewSet.get_queryset: {queryset}")
        return queryset

    def create(self, request, *args, **kwargs):
        print(f"FavoritasClienteViewSet.create: dados recebidos {request.data}")
        data = request.data.copy()
        data['usuario'] = request.user.id

        if FavoritasCliente.objects.filter(usuario=request.user, cliente=data['cliente']).exists():
            print("Erro: O cliente já está favoritado.")
            return Response({"detail": "O cliente já está favoritado."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                print(f"FavoritasClienteViewSet.create: favorito criado com sucesso {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                print(f"Erro ao criar favorito: {e}")
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print(f"FavoritasClienteViewSet.create: erros de validação {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = FavoritasCliente.objects.get(id=kwargs['pk'], usuario=request.user)
            print(f"FavoritasClienteViewSet.destroy: tentando deletar favorito {instance}")
            self.perform_destroy(instance)
            print(f"FavoritasClienteViewSet.destroy: favorito deletado com sucesso")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FavoritasCliente.DoesNotExist:
            print("Erro: Favorito não encontrado.")
            return Response({"detail": "Favorito não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Erro ao deletar favorito: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ComentarioViewSet(viewsets.ModelViewSet):
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        ordem_id = self.request.query_params.get('ordemId', None)
        print(f"Buscando comentários para o usuário: {user.username} e ordem: {ordem_id}")
        
        queryset = Comentario.objects.filter(Q(ordem__compartilhamento__usuario_destino=user) | Q(ordem__user=user))

        if ordem_id:
            queryset = queryset.filter(ordem_id=ordem_id)
        
        queryset = queryset.order_by('id')  
        
        print(f"Comentários encontrados: {queryset}")
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        ordem = serializer.validated_data['ordem']

        # Verificar se o usuário tem permissão para adicionar comentários
        compartilhamento = Compartilhamento.objects.filter(ordem=ordem, usuario_destino=user).first()

        if ordem.user != user and (not compartilhamento or compartilhamento.permissao not in ['comentario', 'editor']):
            raise serializers.ValidationError("Você não tem permissão para comentar nesta ordem.")

        try:
            print("Dados recebidos para criar comentário:", serializer.validated_data)
            comentario = serializer.save(usuario=self.request.user)
            print("Comentário criado com sucesso:", comentario)
            return comentario
        except Exception as e:
            print(f"Erro ao criar comentário: {e}")
            raise serializers.ValidationError(f"Erro ao criar comentário: {e}")

    def create(self, request, *args, **kwargs):
        print(f"Recebida solicitação de criação de comentário com os dados: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            comentario = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            print("Comentário salvo com sucesso, respondendo ao cliente.")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            print("Falha na validação do comentário com os erros:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnexoViewSet(viewsets.ModelViewSet):
    serializer_class = AnexoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        ordem_id = self.request.query_params.get('ordem', None)
        print(f"Buscando anexos para o usuário: {user.username} e ordem: {ordem_id}")
        
        queryset = Anexo.objects.filter(Q(ordem__compartilhamento__usuario_destino=user) | Q(ordem__user=user))

        if ordem_id:
            queryset = queryset.filter(ordem_id=ordem_id)
        
        queryset = queryset.order_by('id')  
        
        print(f"Anexos encontrados: {queryset}")
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        ordem = serializer.validated_data['ordem']

        # Verificar se o usuário tem permissão para adicionar anexos
        compartilhamento = Compartilhamento.objects.filter(ordem=ordem, usuario_destino=user).first()

        if ordem.user != user and (not compartilhamento or compartilhamento.permissao not in ['comentario', 'editor']):
            raise serializers.ValidationError("Você não tem permissão para adicionar anexos nesta ordem.")

        try:
            print("Dados recebidos para criar anexo:", serializer.validated_data)
            anexo = serializer.save()
            print("Anexo criado com sucesso:", anexo)
            return anexo
        except Exception as e:
            print(f"Erro ao criar anexo: {e}")
            raise serializers.ValidationError(f"Erro ao criar anexo: {e}")

    def create(self, request, *args, **kwargs):
        print(f"Recebida solicitação de criação de anexo com os dados: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            anexo = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            print("Anexo salvo com sucesso, respondendo ao cliente.")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            print("Falha na validação do anexo com os erros:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   

class CompartilhamentoViewSet(viewsets.ModelViewSet):
    queryset = Compartilhamento.objects.all().order_by('id')
    serializer_class = CompartilhamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(f"[BACKEND] Buscando compartilhamentos para o usuário: {user.username}")
        queryset = Compartilhamento.objects.filter(
            Q(usuario_origem=user) | Q(usuario_destino=user)
        ).distinct()
        print(f"[BACKEND] Compartilhamentos encontrados: {[f'ID: {comp.id}, Usuário Origem: {comp.usuario_origem.username}, Usuário Destino: {comp.usuario_destino.username}' for comp in queryset]}")
        return queryset

    def perform_create(self, serializer):
        usuario_origem = self.request.user
        usuario_destino = serializer.validated_data.get('usuario_destino')
        ordem = serializer.validated_data.get('ordem')

        # Verifique se o usuário de origem realmente é o dono da ordem (comparando com o campo 'user')
        if ordem.user != usuario_origem:
            print(f"[BACKEND] Tentativa de criação de compartilhamento não autorizada. Usuário origem: ID={usuario_origem.id}, Nome={usuario_origem.username}")
            raise serializers.ValidationError("Somente o proprietário da ordem pode compartilhá-la.")
        
        # Continue com a criação se for o dono da ordem
        try:
            print('[BACKEND] Dados recebidos para criação de compartilhamento:', serializer.validated_data)
            compartilhamento = serializer.save(usuario_origem=usuario_origem)
            print(f"[BACKEND] Compartilhamento criado com sucesso. Usuário destino encontrado: ID={usuario_destino.id}, Nome={usuario_destino.username}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[BACKEND] Erro ao criar compartilhamento: {e}")
            raise serializers.ValidationError(f"Erro ao criar compartilhamento: {e}")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user

        if instance.usuario_origem == user or instance.usuario_destino == user:
            print(f"[BACKEND] Permissão concedida para remover compartilhamento: ID={instance.id}")
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            print(f"[BACKEND] Tentativa de remoção de compartilhamento negada para o usuário: ID={user.id}, Nome={user.username}")
            return Response({'detail': 'Você não tem permissão para remover este compartilhamento.'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'])
    def usuarios(self, request, pk=None):
        try:
            print(f"[BACKEND] Buscando usuários para a ordem com ID: {pk}")
            # `pk` é o ID da ordem de serviço
            ordem = Ordem.objects.get(id=pk)
            print(f"[BACKEND] Ordem de serviço encontrada: {ordem.id}")

            compartilhamentos = Compartilhamento.objects.filter(ordem=ordem)
            print(f"[BACKEND] Compartilhamentos encontrados: {compartilhamentos.count()}")

            if not compartilhamentos.exists():
                print(f"[BACKEND] Nenhum compartilhamento encontrado para a ordem com ID {pk}.")
                return Response({"detail": "Nenhum compartilhamento encontrado para esta ordem."}, status=status.HTTP_404_NOT_FOUND)

            usuarios = [comp.usuario_destino for comp in compartilhamentos]
            usuarios_origem = [comp.usuario_origem for comp in compartilhamentos]
            todos_usuarios = list(set(usuarios + usuarios_origem))  # Garantir que todos os usuários (origem e destino) estejam na lista

            if not todos_usuarios:
                print(f"[BACKEND] Nenhum usuário encontrado para a ordem com ID {pk}.")
                return Response({"detail": "Nenhum usuário encontrado."}, status=status.HTTP_404_NOT_FOUND)

            print(f"[BACKEND] Usuários encontrados: {[user.username for user in todos_usuarios]}")

            serializer = UserSerializer(todos_usuarios, many=True)
            return Response(serializer.data)
        except Ordem.DoesNotExist:
            print(f"[BACKEND] Ordem de serviço com ID {pk} não encontrada.")
            return Response({'detail': 'Ordem de serviço não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[BACKEND] Erro ao buscar usuários compartilhados: {e}")
            import traceback
            traceback.print_exc()
            return Response({'detail': 'Erro ao buscar usuários compartilhados.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='permissao')
    def permissao(self, request, pk=None):
        try:
            user = self.request.user
            print(f"[BACKEND] Verificando permissões para o usuário: {user.username} na ordem com ID: {pk}")

            # Tenta encontrar o compartilhamento com base na ordem e no usuário destino
            compartilhamento = Compartilhamento.objects.get(ordem__id=pk, usuario_destino=user)
            print(f"[BACKEND] Permissão encontrada: {compartilhamento.permissao}")

            return Response({'permissao': compartilhamento.permissao})
        except Compartilhamento.DoesNotExist:
            print(f"[BACKEND] Compartilhamento não encontrado para o usuário: {user.username} na ordem com ID: {pk}")
            return Response({'detail': 'Permissão não encontrada para este usuário.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[BACKEND] Erro ao buscar permissão: {e}")
            import traceback
            traceback.print_exc()
            return Response({'detail': 'Erro ao buscar permissão.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RelatorioPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, ordem_id, *args, **kwargs):
        print(f"Solicitação recebida para gerar relatório PDF para a ordem ID: {ordem_id}")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Ordem de Serviço", ln=True, align="C")

        try:
            ordem = Ordem.objects.get(user=request.user, id=ordem_id)
            print(f"Ordem encontrada: ID={ordem.id}, Cliente={ordem.cliente.nome if ordem.cliente else 'Desconhecido'}")
            pdf.cell(200, 10, txt=f"ID: {ordem.id}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Data de Abertura: {ordem.data_abertura.strftime('%d/%m/%Y')}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Status: {ordem.status}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Hardware: {ordem.hardware}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Serviço: {ordem.servico}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Prioridade: {ordem.prioridade}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Descrição: {ordem.descricao}", ln=True, align="L")
            pdf.cell(200, 10, txt=f"Cliente: {ordem.cliente.nome if ordem.cliente else 'Desconhecido'}", ln=True, align="L")
        except Ordem.DoesNotExist:
            print(f"Erro: Ordem de serviço ID {ordem_id} não encontrada.")
            pdf.cell(200, 10, txt="Ordem de serviço não encontrada", ln=True, align="C")

        # Salvar o PDF temporariamente no servidor
        temp_file_path = f'/tmp/relatorio_ordem_{ordem_id}.pdf'
        pdf.output(temp_file_path)
        print(f"PDF salvo em {temp_file_path}")

        # Retornar o PDF como um FileResponse
        return FileResponse(open(temp_file_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"relatorio_ordem_{ordem_id}.pdf")

class NotificacaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            notificacoes = []

            novas_ordens = Ordem.objects.filter(user=user, status='Novo')
            for ordem in novas_ordens:
                notificacoes.append({
                    'id': ordem.id,
                    'tipo': 'Nova Ordem',
                    'detalhes': f'Ordem ID {ordem.id} foi criada.',
                    'lida': False
                })

            ordens_canceladas = Ordem.objects.filter(user=user, status='Cancelada')
            for ordem in ordens_canceladas:
                notificacoes.append({
                    'id': ordem.id,
                    'tipo': 'Ordem Cancelada',
                    'detalhes': f'Ordem ID {ordem.id} foi cancelada.',
                    'lida': False
                })

            ordens_concluidas = Ordem.objects.filter(user=user, status='Concluída')
            for ordem in ordens_concluidas:
                notificacoes.append({
                    'id': ordem.id,
                    'tipo': 'Ordem Concluída',
                    'detalhes': f'Ordem ID {ordem.id} foi concluída.',
                    'lida': False
                })

            compartilhamentos_recebidos = Compartilhamento.objects.filter(usuario_destino=user)
            for compartilhamento in compartilhamentos_recebidos:
                notificacoes.append({
                    'id': compartilhamento.id,
                    'tipo': 'Novo Compartilhamento',
                    'detalhes': f'Ordem ID {compartilhamento.ordem.id} foi compartilhada com você por {compartilhamento.usuario_origem.username}.',
                    'lida': False
                })

            NOTIFICACOES[user.username] = notificacoes
            print(f"[INFO] Notificações retornadas para o usuário {user.username}: {notificacoes}")
            return Response(notificacoes, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"[ERROR] Erro ao obter notificações para o usuário {user.username}: {e}")
            return Response({"detail": "Erro ao obter notificações."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        user = request.user
        try:
            print(f"[INFO] Limpando notificações para o usuário {user.username}")
            NOTIFICACOES[user.username] = []
            print(f"[INFO] Notificações limpas com sucesso para o usuário {user.username}")
            return Response({"detail": "Notificações limpas com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"[ERROR] Erro ao limpar notificações para o usuário {user.username}: {e}")
            return Response({"detail": "Erro ao limpar notificações."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        id = kwargs.get('id')
        try:
            user = request.user
            notificacao_tipo = request.data.get('tipo')
            print(f"[INFO] Marcando notificação como lida. Tipo: {notificacao_tipo}, ID: {id}, Usuário: {user.username}")

            notificacoes = NOTIFICACOES.get(user.username, [])
            for notificacao in notificacoes:
                if notificacao['id'] == id and notificacao['tipo'] == notificacao_tipo:
                    notificacao['lida'] = True
                    break
            NOTIFICACOES[user.username] = notificacoes

            print(f"[INFO] Notificação marcada como lida. Tipo: {notificacao_tipo}, ID: {id}, Usuário: {user.username}")
            return Response({"detail": "Notificação marcada como lida."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"[ERROR] Erro ao marcar notificação como lida para o usuário {user.username} e ID {id}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)