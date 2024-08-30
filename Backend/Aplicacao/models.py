from django.db import models
from django.contrib.auth.models import User as DjangoUser

class Cliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='user_cliente')

    class Meta:
        unique_together = ('cpf', 'user')  

    def __str__(self):
        return self.nome

    
class Ordem(models.Model):
    STATUS_CHOICES = [
        ('Novo', 'Novo'),
        ('Pendente', 'Pendente'),
        ('Em andamento', 'Em andamento'),
        ('Concluída', 'Concluída'),
        ('Cancelada', 'Cancelada'),

    ]
    PRIORIDADE_CHOICES = [
        ('Baixa', 'Baixa'),
        ('Média', 'Média'),
        ('Alta', 'Alta'),
    ]
    HARDWARE_CHOICES = [
        ('Computador', 'Computador'),
        ('Impressora', 'Impressora'),
        ('Celular', 'Celular'),
        ('Notebook', 'Notebook'),
        ('Roteador', 'Roteador'),
    ]
    SERVICO_CHOICES = [
        ('Formatação', 'Formatação'),
        ('Troca de placa', 'Troca de placa'),
        ('Limpeza', 'Limpeza'),
        ('Atualização de Software', 'Atualização de Software'),
        ('Remoção de vírus', 'Remoção de vírus'),
    ]
    id = models.BigAutoField(primary_key=True)
    data_abertura = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Novo')
    hardware = models.CharField(max_length=255, choices=HARDWARE_CHOICES)
    servico = models.CharField(max_length=255, choices=SERVICO_CHOICES)
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='Média')
    descricao = models.TextField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='user_ordens')

    def save(self, *args, **kwargs):
        if self.pk is not None:
            previous_status = Ordem.objects.get(pk=self.pk).status
            if previous_status != 'Novo' and self.status == 'Novo':
                raise ValueError("Não é possível retornar o status para 'Novo'.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ordem {self.id} - {self.cliente.nome}"

class FavoritasCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('cliente', 'usuario')

    def __str__(self):
        return f"Favorito de {self.usuario.username} - Cliente {self.cliente.nome}"

class FavoritasOrdem(models.Model):
    ordem = models.ForeignKey(Ordem, on_delete=models.CASCADE)
    usuario = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('ordem', 'usuario')

    def __str__(self):
        if self.ordem:
            return f"Favorito de {self.usuario.username} - Ordem {self.ordem.id}"

class Comentario(models.Model):
    usuario = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    ordem = models.ForeignKey(Ordem, on_delete=models.CASCADE)
    texto = models.TextField()
    data_comentario = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        print(f"Salvando comentário: {self.texto}")
        super().save(*args, **kwargs)
        print(f"Comentário salvo com sucesso: {self.id}")

    def __str__(self):
        return f"Comentário de {self.usuario.username} em Ordem {self.ordem.id}"

class Anexo(models.Model):
    ordem = models.ForeignKey('Ordem', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to='anexos/')

    def save(self, *args, **kwargs):
        print(f"Salvando anexo para a ordem: {self.ordem.id}")
        super().save(*args, **kwargs)
        print(f"Anexo salvo com sucesso: {self.id}, caminho: {self.arquivo.path}")

    def __str__(self):
        return f"Anexo {self.id} para Ordem {self.ordem.id}"
    
    
class Compartilhamento(models.Model):
    PERMISSOES = [
        ('leitura', 'Somente Leitura'),
        ('comentario', 'Somente Comentário'),
        ('editor', 'Editor'),
    ]

    usuario_origem = models.ForeignKey(DjangoUser, related_name='compartilhamentos_enviados', on_delete=models.CASCADE)
    usuario_destino = models.ForeignKey(DjangoUser, related_name='compartilhamentos_recebidos', on_delete=models.CASCADE)
    ordem = models.ForeignKey(Ordem, related_name='compartilhamento', on_delete=models.CASCADE)
    permissao = models.CharField(max_length=10, choices=PERMISSOES, default='leitura')

    def __str__(self):
        return f"Compartilhamento de {self.usuario_origem.username} para {self.usuario_destino.username} - Ordem {self.ordem.id} - Permissão {self.permissao}"
