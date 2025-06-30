import google.generativeai as genai
from config_loader import load_config
import yaml
import os # Importar a biblioteca os
from service_manager import ServiceManager

class FAQAgent:
    def __init__(self):
        config = load_config()
        self.gemini_api_key = config.get('gemini_api_key')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in config.yaml")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.service_manager = ServiceManager()

        # Carregar a base de conhecimento das variáveis de ambiente e service manager
        services_summary = self.service_manager.get_services_summary()
        self.knowledge_base = (
            f"* **Serviços:** {services_summary}\n"
            f"* **Horário:** {os.getenv('BARBERSHOP_HOURS', 'Segunda a Sexta, das 10h às 14h20 e das 15h20 às 20h. Sábados, das 10h às 14h20 e das 15h20 às 18h. Domingo é nosso dia de descanso!')}\n"
            f"* **Endereço:** {os.getenv('BARBERSHOP_ADDRESS', 'Rua Professor Antônio José Botelho, 333, Sala 4')}\n"
            f"* **Contato:** {os.getenv('BARBERSHOP_CONTACT', 'Não informado')}"
        )

        # Load prompts
        with open('config/prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)
        self.faq_prompt_template = prompts.get('faq_prompt') # Renomeado para indicar que é um template

    def answer_question(self, user_question: str) -> str:
        # Preencher o template do prompt com a base de conhecimento e a pergunta
        prompt = self.faq_prompt_template.format(
            knowledge_base=self.knowledge_base,
            user_question=user_question
        )
        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            return answer
        except Exception as e:
            print(f"Error answering FAQ: {e}")
            return "Desculpe, não consegui encontrar uma resposta para sua pergunta no momento."

