# Use uma imagem base oficial do Python
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia apenas o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Expõe a porta que o Gunicorn usará (a mesma porta que o Flask usa por padrão)
EXPOSE 5000

# Comando para iniciar a aplicação com Gunicorn
# O 'main:app' assume que sua aplicação Flask é uma variável 'app' no arquivo 'main.py'
# No seu caso, a aplicação Flask é definida em whatsapp_webhook.py e o ponto de entrada é run_webhook_server()
# Precisamos ajustar isso para que o Gunicorn possa servir a aplicação Flask corretamente.
# A forma mais comum é ter a instância 'app' do Flask diretamente acessível.
# Vou ajustar o comando para apontar para a instância 'app' definida em whatsapp_webhook.py
CMD ["gunicorn", "whatsapp_webhook:app", "--bind", "0.0.0.0:5000"]
