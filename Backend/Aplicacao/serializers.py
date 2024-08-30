from rest_framework import serializers
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from .models import Cliente, Ordem, Compartilhamento, FavoritasCliente, FavoritasOrdem, Comentario, Anexo

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoUser
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def create(self, validated_data):
        print("Criando usuário com os dados:", validated_data)
        user = DjangoUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        print("Usuário criado com sucesso:", user.username)
        return user

    def update(self, instance, validated_data):
        print("Atualizando usuário:", instance.id)
        print("Dados validados recebidos para atualização:", validated_data)
        try:
            instance.username = validated_data.get('username', instance.username)
            instance.email = validated_data.get('email', instance.email)
            instance.save()
            print("Usuário atualizado com sucesso:", instance.id)
        except Exception as e:
            print(f"Erro ao atualizar o usuário: {e}")
            raise serializers.ValidationError(f"Erro ao atualizar o usuário: {e}")
        return instance

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, data):
        print("Validando login com os dados:", data)
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if not user:
                print("Falha na validação: não foi possível fazer login com as credenciais fornecidas")
                raise serializers.ValidationError(_("Não foi possível fazer login com as credenciais fornecidas."), code='authorization')
        else:
            print("Falha na validação: 'username' e 'password' são obrigatórios")
            raise serializers.ValidationError(_("É necessário incluir 'username' e 'password'."), code='authorization')

        data['user'] = user
        print("Login validado com sucesso para o usuário:", user.username)
        return data

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        self.reset_form = PasswordResetForm(data=self.initial_data)
        if not self.reset_form.is_valid():
            print("Falha na validação do email: formulário de email inválido")
            raise serializers.ValidationError("Email inválido")

        if not DjangoUser.objects.filter(email=value).exists():
            print("Falha na validação do email: nenhum usuário encontrado com este email")
            raise serializers.ValidationError("Nenhum usuário encontrado com este endereço de email")

        return value

    def save(self, **kwargs):
        try:
            print("Tentando salvar reset de senha para o email:", self.validated_data['email'])
            request = self.context.get('request')
            opts = {
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                'from_email': None,
                'email_template_name': 'registration/password_reset_email.html',
                'subject_template_name': 'registration/password_reset_subject.txt',
                'request': request,
            }
            self.reset_form.save(**opts)
            print("Reset de senha salvo com sucesso")
        except Exception as e:
            print(f"Erro ao salvar reset de senha: {e}")
            raise serializers.ValidationError(f"Erro ao tentar resetar a senha: {e}")

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = urlsafe_base64_decode(attrs['uidb64']).decode()
            self.user = DjangoUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, DjangoUser.DoesNotExist):
            raise serializers.ValidationError("O link de reset é inválido.")

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError("O token de reset é inválido ou expirou.")

        return attrs

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_old_password(self, value):
        print("Validando senha antiga")
        user = self.context['request'].user
        if not user.check_password(value):
            print("Falha na validação da senha antiga: senha antiga incorreta")
            raise serializers.ValidationError(_("Senha antiga incorreta"))
        return value

    def save(self, **kwargs):
        print("Salvando alteração de senha")
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        update_session_auth_hash(self.context['request'], user)
        print("Alteração de senha salva com sucesso para o usuário:", user.username)

class ClienteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cliente
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        cpf = data.get('cpf')
        cnpj = data.get('cnpj')
        email = data.get('email')

        if Cliente.objects.filter(user=user, cpf=cpf).exists():
            raise serializers.ValidationError("Este CPF já foi cadastrado por você.")

        if cnpj and Cliente.objects.filter(user=user, cnpj=cnpj).exists():
            raise serializers.ValidationError("Este CNPJ já foi cadastrado por você.")

        if Cliente.objects.filter(user=user, email=email).exists():
            raise serializers.ValidationError("Este email já foi cadastrado por você.")

        return data

class OrdemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordem
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        cliente = data.get('cliente')

        print(f"Validando ordem para o usuário: {user.username}, cliente: {cliente.nome if cliente else 'Nenhum cliente informado'}")

        if user != data['user']:
            raise serializers.ValidationError("Ordem não pertence ao usuário logado.")
        return data

class CompartilhamentoSerializer(serializers.ModelSerializer):
    usuario_origem_nome = serializers.CharField(source='usuario_origem.username', read_only=True)
    permissao = serializers.ChoiceField(choices=Compartilhamento.PERMISSOES, default='leitura')

    class Meta:
        model = Compartilhamento
        fields = '__all__'

    def validate(self, data):
        try:
            print('Validando dados de compartilhamento:', data)

            if Compartilhamento.objects.filter(
                usuario_origem=data['usuario_origem'], 
                usuario_destino=data['usuario_destino'], 
                ordem=data['ordem']
            ).exists():
                raise serializers.ValidationError("Esta ordem já foi compartilhada com este usuário.")
            return data
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Erro na validação do compartilhamento: {e}")
            raise e

        
class FavoritasOrdemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoritasOrdem
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        if FavoritasOrdem.objects.filter(usuario=user, ordem=data['ordem']).exists():
            raise serializers.ValidationError("A ordem já está favoritada.")
        return data

class FavoritasClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoritasCliente
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        if FavoritasCliente.objects.filter(usuario=user, cliente=data['cliente']).exists():
            raise serializers.ValidationError("O cliente já está favoritado.")
        return data

class AnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anexo
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        ordem = data['ordem']

        # Verificar se o usuário é o proprietário da ordem
        if ordem.user == user:
            print("Validação do anexo bem-sucedida para o proprietário da ordem.")
            return data

        # Verificar se o usuário tem uma permissão de compartilhamento para adicionar anexos
        compartilhamento = Compartilhamento.objects.filter(ordem=ordem, usuario_destino=user).first()

        if not compartilhamento or compartilhamento.permissao not in ['comentario', 'editor']:
            print("Erro na validação: Anexo não permitido para este usuário.")
            raise serializers.ValidationError("Você não tem permissão para adicionar anexos nesta ordem.")
        
        print("Validação do anexo bem-sucedida.")
        return data


class ComentarioSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True) 

    class Meta:
        model = Comentario
        fields = '__all__'
        read_only_fields = ['usuario', 'data_comentario']

    def validate(self, data):
        user = self.context['request'].user
        ordem = data['ordem']

        # Verificar se o usuário é o proprietário da ordem
        if ordem.user == user:
            print("Validação do comentário bem-sucedida para o proprietário da ordem.")
            return data

        # Verificar se o usuário tem uma permissão de compartilhamento para adicionar comentários
        compartilhamento = Compartilhamento.objects.filter(ordem=ordem, usuario_destino=user).first()
        
        if not compartilhamento or compartilhamento.permissao not in ['comentario', 'editor']:
            print("Erro na validação: Comentário não permitido para este usuário.")
            raise serializers.ValidationError("Você não tem permissão para comentar nesta ordem.")
        
        print("Validação do comentário bem-sucedida.")
        return data
