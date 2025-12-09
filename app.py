from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import threading
import time
from dateutil import parser
from functools import wraps
import qrcode 
import io
import base64
import os
import json
import logging
import requests
import urllib.parse
import re
from typing import Optional, Tuple, Dict, Any, List
import ssl

# ... outros imports
# 🆕 ADICIONAR ESTE IMPORT:
from realtime_integration import (
    notify_on_status_change,
    notify_on_new_response,
    notify_on_manual_update
)
#------Sistema Autocomplete modal--------
import cliente_autocomplete

#------DISPARADOR---------
import pandas as pd
from werkzeug.utils import secure_filename
import schedule
import threading
import time
import websocket
import sys
import logging
#----------------

# Força o console do Windows a usar UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_bot.log', encoding='utf-8'),  # <- necessário
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_muito_segura_aqui_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

DATABASE = 'reunioes.db'

# Configurações da Evolution API
EVOLUTION_API_CONFIG = {
    'base_url': 'http://82.25.69.24:8090',
    'api_key': 'olvjg1k1ldmbhyl8owi6',  # ← CORRIGIDO: Use a key da imagem
    'instance_name': 'marco_reunioes_bot',
    'webhook_url': 'http://82.25.69.24:3000/webhook/evolution'
}
#---------------------------
'''
def create_instance_with_qr():
    """Cria instância na Evolution API e retorna QR Code"""
    url = f"{EVOLUTION_API_CONFIG['base_url']}/instance/create"
    headers = {
        "apikey": EVOLUTION_API_CONFIG["api_key"],
        "Content-Type": "application/json"
    }
    payload = {
        "instanceName": EVOLUTION_API_CONFIG["instance_name"],
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
        "webhook": EVOLUTION_API_CONFIG["webhook_url"]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    # API retorna o QR Code em Base64 → podemos exibir direto na tela
    if "qrcode" in data:
        qr_base64 = data["qrcode"]
        return qr_base64
    else:
        raise Exception(f"Erro ao criar instância: {data}")
'''
# Endpoint Flask para usuário se conectar
'''
@app.route("/connect")
def connect():
    try:
        qr_code_base64 = create_instance_with_qr()  # supondo que retorne Base64 do QR
        return jsonify({
            "instanceName": "marco_reunioes_bot",
            "qrcode": qr_code_base64,   # enviar a string base64
            "integration": "WHATSAPP-BAILEYS"
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
'''

# ========== IMPORTS (no início do arquivo) ==========
from disparador_massa import disparador_bp, init_disparador_module
from disparador_massa import (
    disparador_bp, 
    init_disparador_module, 
    register_page_route
)

# ========== APÓS criar app = Flask(__name__) ==========
# Registra blueprint
app.register_blueprint(disparador_bp)

# Registra rota da página
register_page_route(app)

# ========== NO if __name__ == '__main__': ==========
# Antes de app.run()
init_disparador_module()

#--------------------------------
class ResponseAnalyzer:
    """Analisa respostas de clientes para determinar confirmação - VERSÃO CORRIGIDA v2"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto removendo acentos e convertendo para minúsculas"""
        import unicodedata
        
        if not text:
            return ""
        
        # Remove acentos
        normalized = unicodedata.normalize('NFKD', text)
        normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
        
        # Lowercase
        return normalized.lower().strip()
    
    @staticmethod
    def analyze_response(message: str) -> Dict[str, Any]:
        """Analisa mensagem e retorna status de confirmação - VERSÃO CORRIGIDA"""
        if not message:
            return {
                'status': 'unclear',
                'confidence': 0.0,
                'scores': {'positive': 0, 'negative': 0, 'reschedule': 0},
                'original_message': message
            }
        
        # CORREÇÃO 1: Normaliza SEMPRE
        message_normalized = ResponseAnalyzer.normalize_text(message)
        
        logger.info(f"🔍 Analisando: '{message}' → Normalizado: '{message_normalized}'")
        
        # CORREÇÃO 2: Listas SEM acentos e ordenadas por especificidade (do maior para o menor)
        confirmacao_positiva = [
            'com certeza', 'ate la', 'nos vemos', 'tudo bem', 'pode ser',
            'confirmado', 'comparecerei', 'perfeito', 'tranquilo', 'concordo',
            'combinado', 'agendado', 'positivo', 'presente', 'estarei',
            'aceito', 'fechado', 'certeza', 'bacana', 'obvio', 'claro',
            'beleza', 'massa', 'confirmo', 'show', 'joia', 'certo',
            'sim', 'ok', 'vou', 'blz', 'yes', 'sure',
            '👍', '✅', '🤝', '😊', '👌', '💪'
        ]
        
        confirmacao_negativa = [
            # FRASES COMPLETAS (PRIORIDADE MÁXIMA) - SEM ACENTOS (normalizado)
            'nao posso', 'nao consigo', 'nao vou poder', 'nao da', 'nao vai dar',
            'nao tenho como', 'impossivel', 'inviavel', 'indisponivel',
            'nao confirmado', 'nao vou confirmar', 'nao posso confirmar',
            'nao consigo confirmar', 'nao da pra confirmar', 
            
            # Negativas contextuais
            'agenda cheia', 'outro compromisso', 'outro dia', 'outra data',
            'ocupado', 'conflito', 'cancelar', 'desmarcar', 'impedimento',
            'sinto muito', 'infelizmente', 'lamento',
            
            # Frases médias
            'nao posso ir', 'nao vou conseguir', 'nao estarei disponivel',
            'nao vai ser possivel', 'nao tenho disponibilidade',
            
            # Palavras individuais (MENOR PRIORIDADE)
            'jamais', 'nunca', 'nao', 'nope', 'no', 'negativo',
            
            # Emojis
            '👎', '❌', '😞', '🚫', '😔'
        ]
        
        reagendamento = [
            'outro horario', 'semana que vem', 'mais tarde', 'nao sei',
            'disponibilidade', 'reagendar', 'remarcar', 'mudanca',
            'proxima', 'possivel', 'alterar', 'trocar', 'duvida',
            'verificar', 'conferir', 'horarios', 'talvez', 'quando',
            'incerto', 'agenda', 'depois'
        ]
        
        score_positivo = 0
        score_negativo = 0
        score_reagendamento = 0
        
        # CORREÇÃO 3: Verifica do mais específico para o menos específico
        for palavra in confirmacao_positiva:
            if palavra in message_normalized:
                # Peso proporcional ao tamanho da palavra
                peso = max(2, len(palavra.split()))  # Frases valem mais
                score_positivo += peso
                logger.debug(f"  ✅ Encontrado '{palavra}' → +{peso} positivo")
        
        for palavra in confirmacao_negativa:
            if palavra in message_normalized:
                peso = max(2, len(palavra.split()))
                score_negativo += peso
                logger.debug(f"  ❌ Encontrado '{palavra}' → +{peso} negativo")
        
        for palavra in reagendamento:
            if palavra in message_normalized:
                peso = max(1, len(palavra.split()))
                score_reagendamento += peso
                logger.debug(f"  🔄 Encontrado '{palavra}' → +{peso} reagendar")
        
        # CORREÇÃO 4: Respostas ultra-curtas têm peso EXTRA
        if len(message_normalized.strip()) <= 5:
            if message_normalized in ['sim', 'ok', 'yes', 'claro']:
                score_positivo += 10  # Peso MASSIVO
                logger.debug(f"  🎯 Resposta curta POSITIVA detectada → +10")
            elif message_normalized in ['nao', 'no', 'nope', 'nunca', 'jamais']:
                score_negativo += 10  # Peso MASSIVO
                logger.debug(f"  🎯 Resposta curta NEGATIVA detectada → +10")
        
        # CORREÇÃO 5: Cálculo de status com thresholds claros
        total_score = score_positivo + score_negativo + score_reagendamento
        
        if total_score == 0:
            status = 'unclear'
            confidence = 0.0
        elif score_positivo > score_negativo and score_positivo > score_reagendamento:
            status = 'confirmed'
            # Confiança proporcional: quanto maior o score, mais confiança
            confidence = min(0.5 + (score_positivo / (total_score + 1)) * 0.5, 1.0)
        elif score_negativo > score_positivo and score_negativo > score_reagendamento:
            status = 'declined'
            confidence = min(0.5 + (score_negativo / (total_score + 1)) * 0.5, 1.0)
        elif score_reagendamento > 0 and score_reagendamento >= max(score_positivo, score_negativo):
            status = 'reschedule'
            confidence = min(0.4 + (score_reagendamento / (total_score + 1)) * 0.4, 0.9)
        else:
            status = 'unclear'
            confidence = 0.2
        
        result = {
            'status': status,
            'confidence': confidence,
            'scores': {
                'positive': score_positivo,
                'negative': score_negativo,
                'reschedule': score_reagendamento
            },
            'original_message': message
        }
        
        logger.info(f"💭 RESULTADO: {status.upper()} (confiança: {confidence:.2%}) | Scores: P={score_positivo} N={score_negativo} R={score_reagendamento}")
        
        return result

# CORREÇÃO 1: Substitua COMPLETAMENTE a classe EvolutionAPIManager
class EvolutionAPIManager:
    """VERSÃO CORRIGIDA - Resolver erro de instância duplicada"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.instance_name = config['instance_name']
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.webhook_url = config['webhook_url']
        self.session = requests.Session()
        
        # Headers exatos do teste que funcionou
        self.session.headers.update({
            'Content-Type': 'application/json',
            'apikey': self.api_key,
            'Accept': 'application/json'
        })
        self.connected = False
        self.qr_code = None

    def _make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 15) -> Tuple[bool, Dict]:
        """Requisição com logs detalhados para debug"""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"🔍 Testando: {endpoint}")

            kwargs = {'timeout': timeout}
            if method.upper() in ['POST', 'PUT']:
                kwargs['json'] = data
            elif method.upper() == 'GET' and data:
                kwargs['params'] = data

            response = getattr(self.session, method.lower())(url, **kwargs)
            
            logger.info(f"   Status: {response.status_code}")

            # CORREÇÃO CRÍTICA: Verifica se retornou HTML (endpoint errado)
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                logger.error(f"❌ ENDPOINT RETORNOU HTML! Provavelmente endpoint errado: {endpoint}")
                return False, {"error": f"Endpoint {endpoint} retornou HTML em vez de JSON"}

            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    if response.status_code == 200:
                        logger.info(f"✅ SUCESSO: {endpoint}")
                    elif response.status_code == 201:
                        logger.info(f"✅ Mensagem enviada com sucesso!")
                    
                    return True, result
                except ValueError as e:
                    logger.error(f"❌ Erro ao parsear JSON: {e}")
                    return False, {"error": f"Resposta inválida: {response.text}"}
            else:
                error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                logger.error(f"❌ HTTP {response.status_code}: {error_text}")
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}

        except requests.exceptions.Timeout:
            logger.error("⏰ Timeout na requisição")
            return False, {"error": "Timeout na requisição"}
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Erro de conexão")
            return False, {"error": "Erro de conexão com Evolution API"}
        except Exception as e:
            logger.error(f"💥 Erro interno: {e}")
            return False, {"error": f"Erro interno: {str(e)}"}

    def check_existing_instance(self) -> Tuple[bool, str]:
        """CORREÇÃO: Verifica instância existente sem tentar criar"""
        try:
            logger.info(f"🔍 Verificando instância existente: {self.instance_name}")
            
            success, result = self._make_request('GET', '/instance/fetchInstances')
            if not success:
                logger.error(f"❌ Falha ao buscar instâncias: {result}")
                return False, f"Erro ao buscar instâncias: {result.get('error', 'Erro desconhecido')}"
            
            if not isinstance(result, list):
                logger.error(f"❌ Resposta não é uma lista: {type(result)}")
                return False, "Resposta inesperada da API"
            
            logger.info(f"📊 Total de instâncias encontradas: {len(result)}")
            
            # Procura nossa instância na estrutura correta
            for inst in result:
                instance_data = inst.get('instance', {})
                instance_name = instance_data.get('instanceName')
                
                if instance_name == self.instance_name:
                    status = instance_data.get('status', 'unknown')
                    owner = instance_data.get('owner', 'N/A')
                    profile_name = instance_data.get('profileName', 'N/A')
                    
                    logger.info(f"✅ Instância encontrada!")
                    logger.info(f"   📱 Nome: {instance_name}")
                    logger.info(f"   📊 Status: {status}")
                    logger.info(f"   👤 Owner: {owner}")
                    logger.info(f"   🏷️ Profile: {profile_name}")
                    
                    if status == 'open':
                        self.connected = True
                        return True, f"Instância '{self.instance_name}' conectada e pronta"
                    else:
                        self.connected = False
                        return False, f"Instância '{self.instance_name}' encontrada mas status: {status}"
            
            logger.warning(f"❌ Instância '{self.instance_name}' não encontrada na lista")
            return False, f"Instância '{self.instance_name}' não existe"
                
        except Exception as e:
            logger.error(f"💥 Erro ao verificar instância: {e}")
            return False, f"Erro interno: {str(e)}"

    def connect_existing_instance(self) -> Tuple[bool, str]:
        """CORREÇÃO: NÃO tenta conectar - apenas verifica se existe"""
        try:
            logger.info(f"🔗 Verificando instância existente: {self.instance_name}")
            
            # APENAS verifica - NÃO tenta conectar
            instance_exists, message = self.check_existing_instance()
            
            if instance_exists:
                logger.info("✅ Instância já existe e está funcional")
                self.connected = True
                return True, "Instância encontrada e funcional"
            else:
                return False, f"Instância '{self.instance_name}' não encontrada: {message}"
                    
        except Exception as e:
            logger.error(f"💥 Erro ao verificar instância: {e}")
            return False, f"Erro interno: {str(e)}"

    def get_qr_code(self) -> str:
        """CORREÇÃO: Retorna None - instância já deve estar conectada"""
        try:
            logger.info("⚠️ QR Code solicitado, mas instância já deve estar conectada")
            logger.info("💡 Use o Evolution Manager para conectar via QR se necessário")
            return None
        except Exception as e:
            logger.error(f"Erro: {e}")
        return None

    def normalize_phone_number(self, phone: str) -> str:
        """Normalização de telefone"""
        if not phone:
            return ""
        
        # Remove tudo exceto números
        clean_phone = re.sub(r'\D', '', str(phone))
        
        # Lógica brasileira
        if len(clean_phone) == 11 and clean_phone.startswith(('11', '21', '31', '41', '51', '61', '71', '81', '91')):
            # Formato: 21982161008 → 5521982161008
            return '55' + clean_phone
        
        elif len(clean_phone) == 13 and clean_phone.startswith('55'):
            # Já está correto: 5521982161008
            return clean_phone
        
        elif len(clean_phone) == 10 and clean_phone.startswith(('11', '21', '31', '41', '51', '61', '71', '81', '91')):
            # Formato antigo: 2182161008 → 552198216100 (adiciona 55 + 9)
            ddd = clean_phone[:2]
            numero = clean_phone[2:]
            return f"55{ddd}9{numero}"
        
        else:
            logger.warning(f"Formato não reconhecido: {clean_phone}")
            return clean_phone

    def send_message(self, phone: str, message: str) -> Tuple[bool, str]:
        """CORREÇÃO FINAL: Envia mensagem SEM tentar criar/conectar instância"""
        try:
            logger.info(f"📤 Enviando mensagem para {phone}")
            
            # Normaliza telefone
            normalized_phone = self.normalize_phone_number(phone)
            logger.info(f"📞 Telefone normalizado: {normalized_phone}")
            
            # CORREÇÃO: REMOVE TODAS as verificações de conexão que podem tentar criar instância
            # Vai direto para o envio usando a instância que JÁ EXISTE
            
            # Payload correto
            payload = {
                "number": normalized_phone,
                "textMessage": {
                    "text": message
                }
            }
            
            endpoint = f'/message/sendText/{self.instance_name}'
            
            logger.info(f"🔗 Enviando direto para: {endpoint}")
            
            # Envia mensagem DIRETO - sem verificações
            success, result = self._make_request('POST', endpoint, payload)
            
            if success:
                logger.info("🎉 MENSAGEM ENVIADA COM SUCESSO!")
                return True, "Mensagem enviada com sucesso"
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                logger.error(f"❌ FALHA NO ENVIO: {error_msg}")
                return False, error_msg
                    
        except Exception as e:
            error_msg = f"Erro interno no envio: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return False, error_msg

    def restart_instance(self) -> Tuple[bool, str]:
        """Reiniciar instância existente"""
        try:
            success, result = self._make_request('PUT', f'/instance/restart/{self.instance_name}')
            if success:
                self.connected = False
                return True, "Instância reiniciada com sucesso"
            return False, result.get('error', 'Erro ao reiniciar')
        except Exception as e:
            return False, f"Erro crítico: {str(e)}"

    def delete_instance(self) -> Tuple[bool, str]:
        """CUIDADO: Deleta instância (use apenas se necessário)"""
        try:
            success, result = self._make_request('DELETE', f'/instance/delete/{self.instance_name}')
            if success:
                self.connected = False
                return True, "Instância deletada com sucesso"
            return False, result.get('error', 'Erro ao deletar')
        except Exception as e:
            return False, f"Erro crítico: {str(e)}"

    def check_connection_status(self) -> Tuple[bool, str]:
        """Verifica status de conexão"""
        return self.check_existing_instance()

    def get_instance_status(self) -> Tuple[bool, Dict]:
        """Status da instância"""
        return self.check_existing_instance()

    def get_user_info(self) -> Dict:
        """Info do usuário"""
        try:
            success, result = self._make_request('GET', f'/chat/whatsappNumbers/{self.instance_name}')
            return result if success else {"error": result.get('error', 'Erro desconhecido')}
        except Exception as e:
            return {"error": f"Erro crítico: {str(e)}"}

    def health_check(self) -> Dict:
        """Health check"""
        try:
            success, result = self._make_request('GET', '/instance/fetchInstances', timeout=5)
            
            if not success:
                return {
                    "healthy": False,
                    "api_reachable": False,
                    "error": result.get('error', 'API não acessível')
                }
            
            instance_ok, instance_msg = self.check_existing_instance()
            
            return {
                "healthy": instance_ok,
                "api_reachable": True,
                "instance_exists": instance_ok,
                "instance_connected": self.connected,
                "instance_message": instance_msg,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "api_reachable": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def send_message_with_retry(self, phone: str, message: str, max_retries: int = 3) -> Tuple[bool, str]:
        """Retry automático"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Tentativa {attempt + 1}/{max_retries} de envio para {phone}")
                
                success, result = self.send_message(phone, message)
                
                if success:
                    logger.info(f"✅ Sucesso na tentativa {attempt + 1}")
                    return True, result
                
                if "não existe no WhatsApp" in result:
                    return False, result
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Tentativa {attempt + 1} falhou: {result}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Falha definitiva após {max_retries} tentativas: {result}")
                    return False, f"Falha após {max_retries} tentativas: {result}"
                    
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return False, f"Erro após {max_retries} tentativas: {str(e)}"
                time.sleep(2)
        
        return False, f"Falha após {max_retries} tentativas"
    
class WhatsAppMonitor:
    """Monitor para capturar respostas do WhatsApp via webhook - VERSÃO COMPLETA CORRIGIDA"""
    
    def __init__(self, evolution_manager):
        self.evolution_manager = evolution_manager
        self.monitoring = False
        self.monitored_phones = set()
        logger.info("Monitor WhatsApp inicializado")
    
    def start_monitoring(self):
        """Inicia monitoramento de respostas"""
        self.monitoring = True
        logger.info("✅ Monitoramento de respostas ATIVADO")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring = False
        logger.info("❌ Monitoramento de respostas PARADO")
    
    def add_phone_to_monitor(self, phone: str, meeting_id: int):
        """Adiciona telefone para monitoramento com logs detalhados"""
        normalized_phone = self.evolution_manager.normalize_phone_number(phone)
        phone_clean = normalized_phone.replace('@s.whatsapp.net', '')
        
        # Remove duplicatas do mesmo meeting_id
        self.monitored_phones = {(p, mid) for p, mid in self.monitored_phones if mid != meeting_id}
        
        # Adiciona o novo telefone
        self.monitored_phones.add((phone_clean, meeting_id))
        
        logger.info(f"📱 ADICIONADO AO MONITORAMENTO: {phone_clean} (reunião {meeting_id})")
        logger.info(f"📊 Total monitorado agora: {len(self.monitored_phones)}")
        logger.info(f"📋 Lista completa: {list(self.monitored_phones)}")
        
        # Auto-inicia monitoramento se não estiver ativo
        if not self.monitoring:
            self.start_monitoring()
            logger.info("🚀 Monitoramento auto-iniciado")
    
    def process_webhook_message(self, webhook_data: Dict) -> bool:
        """Processa mensagem - VERSÃO CORRIGIDA COM LOGS DETALHADOS"""
        try:
            logger.info(f"📥 Processando webhook...")
            logger.info(f"📊 Estrutura: {json.dumps(webhook_data, indent=2)[:300]}...")
            
            # Extração robusta
            from_number = None
            message_text = None
            
            # Estratégia 1: Estrutura padrão Evolution v2
            key_info = webhook_data.get('key', {})
            from_number = key_info.get('remoteJid') or key_info.get('from')
            
            message_info = webhook_data.get('message', {})
            message_text = (
                message_info.get('conversation') or
                message_info.get('extendedTextMessage', {}).get('text') or
                message_info.get('text') or
                message_info.get('imageMessage', {}).get('caption') or
                message_info.get('videoMessage', {}).get('caption')
            )
            
            # Estratégia 2: Fallback para formato direto
            if not (from_number and message_text):
                from_number = webhook_data.get('from') or webhook_data.get('remoteJid')
                message_text = webhook_data.get('body') or webhook_data.get('text')
            
            # Validação
            if not from_number:
                logger.warning(f"❌ 'from_number' não encontrado")
                logger.info(f"📋 Keys disponíveis: {list(webhook_data.keys())}")
                return False
            
            if not message_text:
                logger.warning(f"❌ 'message_text' não encontrado")
                logger.info(f"📋 Message keys: {list(message_info.keys())}")
                return False
            
            logger.info(f"📱 De: {from_number}")
            logger.info(f"💬 Texto: {message_text}")
            
            # Normalização e busca
            from_number_clean = self._normalize_phone_robust(from_number)
            logger.info(f"📱 Normalizado: {from_number_clean}")
            
            matching_entry = self._find_matching_phone_improved(from_number_clean)
            
            if not matching_entry:
                logger.info(f"⚠️ Número não monitorado: {from_number_clean}")
                logger.info(f"📋 Monitorados: {[p[0] for p in self.monitored_phones]}")
                return False
            
            meeting_id = matching_entry[1]
            logger.info(f"🎯 MATCH! Reunião: {meeting_id}")
            
            # Análise e salvamento
            analysis = ResponseAnalyzer.analyze_response(message_text)
            logger.info(f"📊 Status: {analysis['status']} (confiança: {analysis['confidence']:.2%})")
            
            response_id = self._save_client_response_improved(
                meeting_id=meeting_id,
                response_text=message_text,
                status=analysis['status'],
                confidence=analysis['confidence'],
                analysis_data=analysis
            )
            
            if not response_id:
                logger.error("❌ Falha ao salvar resposta")
                return False
            
            # Atualiza reunião se confiança suficiente
            if analysis['confidence'] >= 0.15:
                success = self._update_meeting_status_improved(meeting_id, analysis['status'], response_id)
                
                if success:
                    logger.info(f"✅ Reunião {meeting_id} atualizada para: {analysis['status']}")
                    
                    if analysis['status'] in ['confirmed', 'declined']:
                        self._remove_from_monitoring(meeting_id)
                else:
                    logger.error(f"❌ Falha ao atualizar reunião {meeting_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Erro no processamento: {e}")
            import traceback
            logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
            return False

    def _save_client_response_improved(self, meeting_id: int, response_text: str, status: str, confidence: float, analysis_data: dict) -> Optional[int]:
        """Salva resposta do cliente com verificação de duplicatas"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                
                # Verifica se já existe resposta idêntica nos últimos 5 minutos
                cursor.execute('''
                    SELECT id FROM client_responses 
                    WHERE meeting_id = ? 
                    AND response_text = ?
                    AND datetime(received_at) >= datetime('now', '-5 minutes')
                    LIMIT 1
                ''', (meeting_id, response_text))
                
                existing = cursor.fetchone()
                if existing:
                    logger.info(f"⚠️ Resposta duplicada ignorada (ID existente: {existing[0]})")
                    return existing[0]
                
                # Insere nova resposta
                cursor.execute('''
                    INSERT INTO client_responses (meeting_id, response_text, status, confidence, analysis_data, received_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (meeting_id, response_text, status, confidence, json.dumps(analysis_data), datetime.now().isoformat()))
                
                response_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"💾 Resposta salva com ID: {response_id}")
                return response_id
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resposta: {e}")
            return None


    def _normalize_phone_robust(self, phone_input):
        """Normalização robusta IDÊNTICA ao evolution_manager"""
        if not phone_input:
            return ""
        
        # Remove @s.whatsapp.net se presente
        if '@' in str(phone_input):
            phone_clean = str(phone_input).split('@')[0]
        else:
            phone_clean = str(phone_input)
        
        # Remove tudo exceto números
        digits_only = re.sub(r'\D', '', phone_clean)
        
        # Remove códigos duplicados
        if digits_only.startswith('5555'):
            digits_only = digits_only[2:]
        
        logger.info(f"🔄 Normalização: '{phone_input}' → '{digits_only}'")
        return digits_only
    
    # CORREÇÃO CRÍTICA: Adicione estes métodos na classe WhatsAppMonitor

    def _find_matching_phone_improved(self, from_number_clean):
        """MÉTODO QUE ESTAVA FALTANDO - Busca correspondência melhorada"""
        logger.info(f"🔍 Buscando match melhorado para: {from_number_clean}")
        
        for monitored_phone, meeting_id in self.monitored_phones:
            monitored_clean = self._normalize_phone_robust(monitored_phone)
            
            logger.info(f"   Comparando: {from_number_clean} vs {monitored_clean}")
            
            # Estratégias de comparação (da mais específica para mais genérica)
            strategies = [
                # 1. Igualdade exata
                lambda f, m: f == m,
                
                # 2. Últimos 11 dígitos (celular brasileiro com DDD)
                lambda f, m: len(f) >= 11 and len(m) >= 11 and f[-11:] == m[-11:],
                
                # 3. Últimos 10 dígitos (número sem código país)
                lambda f, m: len(f) >= 10 and len(m) >= 10 and f[-10:] == m[-10:],
                
                # 4. Últimos 9 dígitos (número sem DDD)
                lambda f, m: len(f) >= 9 and len(m) >= 9 and f[-9:] == m[-9:],
                
                # 5. Um contém o outro (mínimo 9 dígitos)
                lambda f, m: len(min(f, m)) >= 9 and (f in m or m in f),
                
                # 6. Diferença apenas no 9 (celular)
                lambda f, m: (len(f) == 13 and len(m) == 12 and f[:4] + f[5:] == m) or
                            (len(m) == 13 and len(f) == 12 and m[:4] + m[5:] == f)
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    if strategy(from_number_clean, monitored_clean):
                        logger.info(f"🎯 MATCH via estratégia {i+1}!")
                        return (monitored_phone, meeting_id)
                except:
                    continue
        
        logger.info(f"❌ Nenhum match encontrado")
        return None

    def _update_meeting_status_improved(self, meeting_id: int, status: str, response_id: int) -> bool:
        """Atualiza status da reunião - MÉTODO QUE ESTAVA FALTANDO"""
        try:
            logger.info(f"🔄 DEBUG: Atualizando reunião {meeting_id} para {status}")
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                
                # Busca reunião atual
                cursor.execute('SELECT id, titulo, status_confirmacao FROM reunioes WHERE id = ?', (meeting_id,))
                current = cursor.fetchone()
                
                if not current:
                    logger.error(f"❌ Reunião {meeting_id} não existe")
                    return False
                
                old_status = current[2]
                
                # Atualiza status
                cursor.execute('UPDATE reunioes SET status_confirmacao = ? WHERE id = ?', (status, meeting_id))
                rows = cursor.rowcount
                conn.commit()
                
                logger.info(f"✅ Status atualizado: {old_status} → {status} ({rows} linha(s))")
                return rows > 0
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar: {e}")
            return False
        
    def _find_matching_phone(self, from_number_clean):
        """Busca correspondência com múltiplas estratégias - MÉTODO QUE ESTAVA FALTANDO"""
        logger.info(f"🔍 Buscando match para: {from_number_clean}")
        
        for monitored_phone, meeting_id in self.monitored_phones:
            monitored_clean = self._normalize_phone_robust(monitored_phone)
            
            logger.info(f"   Comparando: {from_number_clean} vs {monitored_clean}")
            
            # Estratégias de comparação (da mais específica para mais genérica)
            strategies = [
                # 1. Igualdade exata
                lambda f, m: f == m,
                
                # 2. Últimos 11 dígitos (celular brasileiro com DDD)
                lambda f, m: len(f) >= 11 and len(m) >= 11 and f[-11:] == m[-11:],
                
                # 3. Últimos 10 dígitos (número sem código país)
                lambda f, m: len(f) >= 10 and len(m) >= 10 and f[-10:] == m[-10:],
                
                # 4. Últimos 9 dígitos (número sem DDD)
                lambda f, m: len(f) >= 9 and len(m) >= 9 and f[-9:] == m[-9:],
                
                # 5. Um contém o outro (mínimo 9 dígitos)
                lambda f, m: len(min(f, m)) >= 9 and (f in m or m in f),
                
                # 6. Diferença apenas no 9 (celular)
                lambda f, m: (len(f) == 13 and len(m) == 12 and f[:4] + f[5:] == m) or
                            (len(m) == 13 and len(f) == 12 and m[:4] + m[5:] == f)
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    if strategy(from_number_clean, monitored_clean):
                        logger.info(f"🎯 MATCH via estratégia {i+1}!")
                        return (monitored_phone, meeting_id)
                except:
                    continue
        
        logger.info(f"❌ Nenhum match encontrado")
        return None
        
    def _remove_from_monitoring(self, meeting_id: int):
        """Remove reunião do monitoramento"""
        before_count = len(self.monitored_phones)
        self.monitored_phones = {(phone, mid) for phone, mid in self.monitored_phones if mid != meeting_id}
        after_count = len(self.monitored_phones)
        
        if before_count > after_count:
            logger.info(f"✅ Reunião {meeting_id} removida do monitoramento ({before_count} -> {after_count})")
            logger.info(f"📊 Telefones ainda monitorados: {list(self.monitored_phones)}")
        else:
            logger.warning(f"⚠️ Reunião {meeting_id} não encontrada para remoção do monitoramento")
    
    def get_monitoring_status(self):
        """Retorna status atual do monitoramento"""
        return {
            'monitoring_active': self.monitoring,
            'monitored_count': len(self.monitored_phones),
            'monitored_phones': list(self.monitored_phones)
        }
    
    def clear_all_monitoring(self):
        """Limpa todo o monitoramento (útil para debug)"""
        before_count = len(self.monitored_phones)
        self.monitored_phones.clear()
        logger.info(f"🧹 Monitoramento limpo: {before_count} telefones removidos")

class MessageTemplateManager:
    """Gerenciador de templates de mensagem"""
    
    @staticmethod
    def get_default_template() -> str:
        """Retorna template padrão otimizado"""
        return """🤝 Olá, {nome_convidado}!

**Confirmação de Reunião**
**Data:** {data_reuniao}
**Horário:** {hora_reuniao}
**Assunto:** {assunto}
**Cliente:** {nome_cliente}
**Local:** {local_reuniao}

{link_reuniao}

Por favor, confirme sua presença respondendo esta mensagem com "SIM" ou "NÃO".

Atenciosamente,
**Equipe 2D Consultores** ✨"""
    
    @staticmethod
    def save_template(template: str) -> bool:
        """Salva template no banco com validação"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM whatsapp_config')
                cursor.execute(
                    'INSERT INTO whatsapp_config (template_message) VALUES (?)', 
                    (template,)
                )
                conn.commit()
                logger.info("Template salvo com sucesso")
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar template: {e}")
            return False
    
    @staticmethod
    def load_template() -> str:
        """Carrega template do banco"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT template_message FROM whatsapp_config ORDER BY id DESC LIMIT 1')
                result = cursor.fetchone()
                
                if result and result[0]:
                    return result[0]
                else:
                    # Salva e retorna template padrão
                    default = MessageTemplateManager.get_default_template()
                    MessageTemplateManager.save_template(default)
                    return default
        except Exception as e:
            logger.error(f"Erro ao carregar template: {e}")
            return MessageTemplateManager.get_default_template()
    
    @staticmethod
    def format_message(template: str, meeting_data: Dict[str, Any]) -> str:
        """Formata mensagem substituindo placeholders - VERSÃO CORRIGIDA"""
        try:
            # Parse da data/hora
            data_hora = meeting_data.get('data_hora', '')
            data_obj = parser.parse(data_hora)
            data_formatada = data_obj.strftime('%d/%m/%Y')
            hora_formatada = data_obj.strftime('%H:%M')
            
            # Monta link da reunião se existir
            link_reuniao = ""
            if meeting_data.get('link'):
                link_reuniao = f"🔗 **Link da Reunião:** {meeting_data['link']}"
            
            # MAPEAMENTO CORRETO dos placeholders
            replacements = {
                '{nome_convidado}': meeting_data.get('convidado', ''),
                '{data_reuniao}': data_formatada,
                '{hora_reuniao}': hora_formatada,
                '{assunto}': meeting_data.get('assunto', ''),
                '{nome_cliente}': meeting_data.get('nome_cliente', ''),
                '{local_reuniao}': meeting_data.get('local_reuniao', 'A definir'),
                '{link_reuniao}': link_reuniao
            }
            
            # Substitui cada placeholder
            formatted_message = template
            for placeholder, value in replacements.items():
                formatted_message = formatted_message.replace(placeholder, str(value) if value else '')
            
            return formatted_message
            
        except Exception as e:
            logger.error(f"Erro ao formatar mensagem: {e}")
            return template

class AutoMessageSender:
    """Classe para envio automático de mensagens em background"""
    
    @staticmethod
    def send_confirmation_message_async(meeting_id: int, delay_seconds: int = 2):
        """Envia mensagem de confirmação de forma assíncrona"""
        def _send_message():
            try:
                # Aguarda um pouco para garantir que a reunião foi salva
                time.sleep(delay_seconds)
                
                # Busca dados da reunião
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
                    meeting = cursor.fetchone()
                    
                    if not meeting:
                        logger.error(f"Reunião {meeting_id} não encontrada para envio automático")
                        return
                
                # Verifica se tem telefone
                telefone_cliente = meeting[7] if len(meeting) > 7 else None
                if not telefone_cliente:
                    logger.warning(f"Reunião {meeting_id} sem telefone - não enviando confirmação automática")
                    return
                
                # Verifica se WhatsApp está conectado
                connected, _ = evolution_manager.check_connection_status()
                if not connected:
                    logger.warning(f"WhatsApp não conectado - não enviando confirmação automática para reunião {meeting_id}")
                    # Salva tentativa no log mesmo sem enviar
                    log_whatsapp_message(
                        meeting_id=meeting_id,
                        phone=telefone_cliente,
                        message="[AUTOMÁTICO] Tentativa de envio - WhatsApp não conectado",
                        status="failed",
                        error_message="WhatsApp não estava conectado no momento do envio automático"
                    )
                    return
                
                # Prepara dados para formatação
                meeting_data = {
                    'id': meeting[0],
                    'titulo': meeting[1],
                    'convidado': meeting[2],
                    'data_hora': meeting[3],
                    'assunto': meeting[4],
                    'link': meeting[5] or '',
                    'nome_cliente': meeting[6] or '',
                    'telefone_cliente': telefone_cliente,
                    'local_reuniao': meeting[8] if len(meeting) > 8 else ''
                }
                
                # Carrega e formata template
                template = MessageTemplateManager.load_template()
                formatted_message = MessageTemplateManager.format_message(template, meeting_data)
                
                # Adiciona indicador de mensagem automática
                formatted_message = "" + formatted_message
                
                # Normaliza telefone
                normalized_phone = evolution_manager.normalize_phone_number(telefone_cliente)
                
                logger.info(f"Enviando confirmação automática para reunião {meeting_id}, telefone: {normalized_phone}")
                
                # Envia mensagem
                success, result_message = evolution_manager.send_message(telefone_cliente, formatted_message)
                
                # Registra log
                log_whatsapp_message(
                    meeting_id=meeting_id,
                    phone=normalized_phone,
                    message=formatted_message,
                    status="success" if success else "failed",
                    error_message=None if success else result_message
                )
                
                if success:
                    logger.info(f"Confirmação automática enviada com sucesso para reunião {meeting_id}")
                    
                    # Adiciona telefone ao monitoramento para capturar resposta
                    whatsapp_monitor.add_phone_to_monitor(telefone_cliente, meeting_id)
                    
                else:
                    logger.error(f"Falha no envio automático para reunião {meeting_id}: {result_message}")
                    
            except Exception as e:
                logger.error(f"Erro no envio automático para reunião {meeting_id}: {e}")
                # Registra erro no log
                try:
                    log_whatsapp_message(
                        meeting_id=meeting_id,
                        phone="",
                        message="[AUTOMÁTICO] Erro no envio",
                        status="error",
                        error_message=f"Erro interno: {str(e)}"
                    )
                except:
                    pass
        
        # Executa em thread separada para não bloquear a resposta
        thread = threading.Thread(target=_send_message, daemon=True)
        thread.start()

# Instâncias globais
evolution_manager = EvolutionAPIManager(EVOLUTION_API_CONFIG)
whatsapp_monitor = WhatsAppMonitor(evolution_manager)

# ==========================
# === BANCO DE DADOS =======
# ==========================
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Verifica e cria/atualiza tabela reunioes
        cursor.execute("PRAGMA table_info(reunioes)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'reunioes' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            cursor.execute('''
                CREATE TABLE reunioes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    convidado TEXT NOT NULL,
                    data_hora TEXT NOT NULL,
                    assunto TEXT NOT NULL,
                    link TEXT,
                    nome_cliente TEXT,
                    telefone_cliente TEXT,
                    local_reuniao TEXT,
                    status_confirmacao TEXT DEFAULT 'pending'
                )
            ''')
            logger.info("Tabela reunioes criada")
        else:
            # Adiciona colunas se não existirem
            if 'local_reuniao' not in colunas:
                cursor.execute('ALTER TABLE reunioes ADD COLUMN local_reuniao TEXT')
                logger.info("Coluna local_reuniao adicionada")
            
            if 'status_confirmacao' not in colunas:
                cursor.execute('ALTER TABLE reunioes ADD COLUMN status_confirmacao TEXT DEFAULT "pending"')
                logger.info("Coluna status_confirmacao adicionada")
        
        # Tabela para configurações do WhatsApp
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_message TEXT,
                last_update DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela para log de mensagens enviadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER,
                phone TEXT,
                message TEXT,
                status TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (meeting_id) REFERENCES reunioes (id)
            )
        ''')
        
        # Tabela de respostas dos clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER,
                response_text TEXT,
                status TEXT,
                confidence REAL,
                analysis_data TEXT,
                received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES reunioes (id)
            )
        ''')

          # Tabela para log de payloads recebidos no webhook
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_incoming_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                event TEXT,
                instance TEXT,
                raw_payload TEXT
            )
        ''')

        # ========== 🆕 TABELA DE EVENTOS ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                tipo TEXT NOT NULL,
                data_inicio TEXT NOT NULL,
                data_fim TEXT NOT NULL,
                local TEXT,
                descricao TEXT,
                participantes TEXT,
                cor TEXT DEFAULT 'amarelo',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        if 'numero_pessoas' not in colunas:
            cursor.execute('ALTER TABLE reunioes ADD COLUMN numero_pessoas INTEGER')
            logger.info("Coluna numero_pessoas adicionada")

        conn.commit()

def ensure_created_at_column():
    """Garante a existência da coluna created_at em reunioes, migrando se necessário."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(reunioes)")
        colunas_existentes = [c[1] for c in cursor.fetchall()]

        if 'created_at' in colunas_existentes:
            return

        # Tenta via ALTER TABLE primeiro
        try:
            cursor.execute('ALTER TABLE reunioes ADD COLUMN created_at TEXT')
            cursor.execute('UPDATE reunioes SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL')
            conn.commit()
            logger.info("Coluna created_at adicionada via ALTER TABLE e populada")
            return
        except sqlite3.OperationalError as e:
            logger.warning(f"ALTER TABLE created_at falhou, migrando tabela: {e}")

        # Migração completa recriando a tabela
        cursor.execute("PRAGMA table_info(reunioes)")
        colunas_existentes = [c[1] for c in cursor.fetchall()]

        sel_local_reuniao = 'local_reuniao' if 'local_reuniao' in colunas_existentes else "'' AS local_reuniao"
        sel_status = 'status_confirmacao' if 'status_confirmacao' in colunas_existentes else "'pending' AS status_confirmacao"

        cursor.execute('PRAGMA foreign_keys = OFF')
        cursor.execute('BEGIN TRANSACTION')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reunioes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                convidado TEXT NOT NULL,
                data_hora TEXT NOT NULL,
                assunto TEXT NOT NULL,
                link TEXT,
                nome_cliente TEXT,
                telefone_cliente TEXT,
                local_reuniao TEXT,
                status_confirmacao TEXT DEFAULT 'pending',
                created_at TEXT
            )
        ''')

        insert_sql = f'''
            INSERT INTO reunioes_new (
                id, titulo, convidado, data_hora, assunto, link, nome_cliente,
                telefone_cliente, local_reuniao, status_confirmacao, created_at
            )
            SELECT
                id, titulo, convidado, data_hora, assunto, link, nome_cliente,
                telefone_cliente, {sel_local_reuniao}, {sel_status}, CURRENT_TIMESTAMP
            FROM reunioes
        '''
        cursor.execute(insert_sql)

        cursor.execute('DROP TABLE reunioes')
        cursor.execute('ALTER TABLE reunioes_new RENAME TO reunioes')

        cursor.execute('COMMIT')
        cursor.execute('PRAGMA foreign_keys = ON')
        logger.info("Tabela reunioes migrada com created_at")

def get_reunioes():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # SELECT explícito - ordem garantida
            cursor.execute("""
                SELECT 
                    id, titulo, convidado, data_hora, assunto, 
                    link, nome_cliente, telefone_cliente, 
                    local_reuniao, status_confirmacao, numero_pessoas
                FROM reunioes 
                ORDER BY data_hora
            """)
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Erro ao buscar reuniões: {e}")
        return []

def salvar_reuniao_db(titulo, convidado, data_hora, departamentos, link, nome_cliente, telefone_cliente, local_reuniao, numero_pessoas=None):
    """VERSÃO CORRIGIDA - Garante created_at e insere a reunião com numero_pessoas"""
    ensure_created_at_column()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reunioes (titulo, convidado, data_hora, assunto, link, nome_cliente, telefone_cliente, local_reuniao, numero_pessoas, status_confirmacao, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (titulo, convidado, data_hora, departamentos, link, nome_cliente, telefone_cliente, local_reuniao, numero_pessoas, 'pending', datetime.now().isoformat()))
        meeting_id = cursor.lastrowid
        logger.info(f"Reunião salva: '{titulo}' para {data_hora} (ID: {meeting_id})")
        conn.commit()
        return meeting_id

def log_whatsapp_message(meeting_id: int, phone: str, message: str, status: str, error_message: str = None):
    """Registra log de mensagem enviada"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO whatsapp_logs (meeting_id, phone, message, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (meeting_id, phone, message, status, error_message))
            conn.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar log: {e}")

def save_client_response(meeting_id: int, response_text: str, status: str, confidence: float, analysis_data: str, received_at: str):
    """Salva resposta do cliente no banco"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO client_responses (meeting_id, response_text, status, confidence, analysis_data, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (meeting_id, response_text, status, confidence, analysis_data, received_at))
            conn.commit()
            logger.info(f"Resposta do cliente salva para reunião {meeting_id}: {status}")
    except Exception as e:
        logger.error(f"Erro ao salvar resposta do cliente: {e}")

def update_meeting_status(meeting_id: int, status: str):
    """Atualiza status de confirmação da reunião - VERSÃO CORRIGIDA"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # CORREÇÃO: Verifica se a reunião existe primeiro
            cursor.execute('SELECT id, titulo, status_confirmacao FROM reunioes WHERE id = ?', (meeting_id,))
            current_meeting = cursor.fetchone()
            
            if not current_meeting:
                logger.error(f"❌ Reunião {meeting_id} não encontrada para atualização")
                return False
            
            old_status = current_meeting[2]
            
            # Atualiza o status
            cursor.execute('''
                UPDATE reunioes 
                SET status_confirmacao = ? 
                WHERE id = ?
            ''', (status, meeting_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                logger.info(f"✅ Status da reunião {meeting_id} atualizado: {old_status} → {status}")
                return True
            else:
                logger.error(f"❌ Nenhuma linha afetada ao atualizar reunião {meeting_id}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar status da reunião {meeting_id}: {e}")
        return False

# =================================
# === AUTENTICAÇÃO / LOGIN ========
# =================================
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logado'):
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        if usuario == 'admin' and senha == '@1234':
            session['logado'] = True
            session.permanent = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===============================
# === ROTAS PRINCIPAIS =========
# ===============================
@app.route('/')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/home')
@login_requerido
def home():
    try:
        reunioes = get_reunioes()
        return render_template('home.html', reunioes=reunioes)
    except Exception as e:
        logger.error(f"Erro ao carregar home: {e}")
        return render_template('home.html', reunioes=[], erro="Erro ao carregar reuniões")

@app.route('/agenda')
@login_requerido
def agenda():
    try:
        reunioes = get_reunioes()
        return render_template('home.html', reunioes=reunioes)
    except Exception as e:
        logger.error(f"Erro ao carregar agenda: {e}")
        return render_template('home.html', reunioes=[], erro="Erro ao carregar agenda")

# FUNÇÃO DE VERIFICAÇÃO DE DUPLICATA (adicione antes da rota)
def verificar_duplicata_recente(titulo, convidado, data_hora, janela_segundos=30):
    """Verifica se há reunião muito similar criada recentemente"""
    try:
        agora = datetime.now()
        inicio_janela = agora - timedelta(seconds=janela_segundos)
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, titulo, convidado, created_at
                FROM reunioes 
                WHERE UPPER(TRIM(titulo)) = UPPER(TRIM(?))
                AND UPPER(TRIM(convidado)) = UPPER(TRIM(?))
                AND datetime(created_at) >= datetime(?)
                ORDER BY created_at DESC
                LIMIT 1
            ''', (titulo, convidado, inicio_janela.isoformat()))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    "duplicata": True,
                    "reuniao_id": resultado[0],
                    "created_at": resultado[3]
                }
            
            return {"duplicata": False}
            
    except Exception as e:
        logger.error(f"Erro ao verificar duplicata recente: {e}")
        return {"duplicata": False}
    
@app.route('/whatsapp/health-check', methods=['GET'])
@login_requerido
def whatsapp_health_check():
    """
    Verifica saúde da Evolution API sem fazer requisições pesadas
    """
    try:
        # CORREÇÃO: Use variáveis ou concatenação simples
        api_url = 'http://82.25.69.24:8090'
        instance_name = 'marco_reunioes_bot'
        api_key = 'olvjg1k1ldmbhyl8owi6'
        
        # Monta URL corretamente
        url = f'{api_url}/instance/connectionState/{instance_name}'
        
        # Tenta conexão simples com timeout curto
        response = requests.get(
            url,
            headers={'apikey': api_key},
            timeout=3  # 3 segundos apenas
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verifica se estado é válido
            state = data.get('instance', {}).get('state')
            healthy = state in ['open', 'connecting']
            
            return jsonify({
                'success': True,
                'healthy': healthy,
                'state': state,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'healthy': False,
                'state': 'error',
                'status_code': response.status_code
            })
            
    except requests.Timeout:
        return jsonify({
            'success': True,
            'healthy': False,
            'state': 'timeout'
        })
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({
            'success': True,
            'healthy': False,
            'state': 'error',
            'error': str(e)
        }), 200  # Retorna 200 mesmo com erro
        
# ROTA ATUALIZADA
@app.route('/agenda/salvar', methods=['POST'])
@login_requerido
def salvar_reuniao():
    try:
        dados = request.get_json()
        logger.info(f"📋 Dados recebidos: {json.dumps(dados, indent=2)}")
        
        if not dados:
            return jsonify({"erro": "Dados não fornecidos"}), 400

        # Extrai dados
        titulo = dados.get('titulo', '').strip()
        convidado = dados.get('convidado', '').strip()
        telefone_cliente = dados.get('telefone_cliente', '').strip()
        auto_envio = dados.get('auto_send_whatsapp', False)
        
        # CORREÇÃO: Processa o campo assunto corretamente
        assunto_raw = dados.get('assunto', '')
        if isinstance(assunto_raw, list):
            assunto_processado = ', '.join(assunto_raw)
        elif isinstance(assunto_raw, str):
            assunto_processado = assunto_raw.strip()
        else:
            assunto_processado = str(assunto_raw) if assunto_raw else ''
        
        logger.info(f"🔍 Assunto processado: '{assunto_processado}' (tipo: {type(assunto_processado)})")
        
        # Verifica duplicatas com tolerância
        timestamp = dados.get('_timestamp')
        client_id = dados.get('_client_id')
        
        # ANTI-DUPLICAÇÃO: Verifica se já foi processada nos últimos 30 segundos
        if timestamp:
            time_diff = time.time() * 1000 - timestamp
            if time_diff > 30000:
                return jsonify({"erro": "Requisição expirada. Tente novamente."}), 400
        
        # Validações básicas
        if not all([titulo, convidado]):
            return jsonify({"erro": "Campos obrigatórios não preenchidos"}), 400
        
        # Validação específica para auto-send
        if auto_envio and not telefone_cliente:
            return jsonify({"erro": "Telefone é obrigatório para envio automático"}), 400
        
        # Verifica data/hora
        data_hora = dados.get('data_hora')
        if not data_hora:
            return jsonify({"erro": "Data e horário são obrigatórios"}), 400

        # 🆕 VALIDAÇÃO DO NÚMERO DE PESSOAS
        numero_pessoas = dados.get('numero_pessoas')
        if numero_pessoas:
            try:
                numero_pessoas = int(numero_pessoas)
                if numero_pessoas < 1 or numero_pessoas > 100:
                    numero_pessoas = None
            except (ValueError, TypeError):
                numero_pessoas = None
        
        try:
            data_reuniao = parser.parse(data_hora)
        except Exception:
            return jsonify({"erro": "Data/horário inválido"}), 400
        
        # 🆕 CORREÇÃO: Passa numero_pessoas para o banco
        meeting_id = salvar_reuniao_db(
            titulo, 
            convidado, 
            dados.get('data_hora'), 
            assunto_processado,
            dados.get('link', ''), 
            dados.get('nome_cliente', ''), 
            telefone_cliente, 
            dados.get('local_reuniao', ''),
            numero_pessoas  # ✅ ADICIONE ESTA LINHA
        )
        logger.info(f"💾 Reunião salva com ID: {meeting_id}")
        
        # CORREÇÃO: Envio automático com assunto corrigido
        if auto_envio and telefone_cliente:
            logger.info(f"🚀 PROCESSANDO ENVIO AUTOMÁTICO para reunião {meeting_id}")
            
            try:
                # Verifica conexão WhatsApp
                connected, status = evolution_manager.check_connection_status()
                if not connected:
                    logger.warning(f"⚠️ WhatsApp não conectado: {status}")
                    return jsonify({
                        "mensagem": "Reunião salva com sucesso!",
                        "auto_send_error": f"WhatsApp não conectado: {status}",
                        "meeting_id": meeting_id
                    })
                
                # CORREÇÃO: Prepara dados da mensagem com assunto corrigido
                meeting_data = {
                    'convidado': convidado,
                    'data_hora': data_hora,
                    'assunto': assunto_processado,
                    'link': dados.get('link', ''),
                    'nome_cliente': dados.get('nome_cliente', ''),
                    'local_reuniao': dados.get('local_reuniao', '')
                }
                
                # Carrega e formata template
                template = MessageTemplateManager.load_template()
                formatted_message = MessageTemplateManager.format_message(template, meeting_data)
                formatted_message = f"{formatted_message}"
                
                # Envio direto (sem timeout complexo)
                success, result = evolution_manager.send_message(telefone_cliente, formatted_message)
                
                # Registra log
                log_whatsapp_message(
                    meeting_id=meeting_id,
                    phone=evolution_manager.normalize_phone_number(telefone_cliente),
                    message=formatted_message,
                    status="success" if success else "failed",
                    error_message=None if success else result
                )
                
                if success:
                    logger.info(f"✅ ENVIO AUTOMÁTICO BEM-SUCEDIDO!")
                    
                    # Adiciona ao monitoramento
                    whatsapp_monitor.add_phone_to_monitor(telefone_cliente, meeting_id)
                    
                    return jsonify({
                        "mensagem": "Reunião salva com sucesso!",
                        "whatsapp_auto_sent": True,
                        "auto_send_status": "success",
                        "meeting_id": meeting_id
                    })
                else:
                    logger.error(f"❌ FALHA no envio automático: {result}")
                    return jsonify({
                        "mensagem": "Reunião salva com sucesso!",
                        "auto_send_error": result,
                        "meeting_id": meeting_id
                    })
                
            except Exception as e:
                logger.error(f"💥 ERRO no envio automático: {e}")
                
                log_whatsapp_message(
                    meeting_id=meeting_id,
                    phone=telefone_cliente,
                    message="[AUTOMÁTICO] Erro crítico",
                    status="error",
                    error_message=str(e)
                )
                
                return jsonify({
                    "mensagem": "Reunião salva com sucesso!",
                    "auto_send_error": f"Erro: {str(e)}",
                    "meeting_id": meeting_id
                })
        
        # Sem auto-send
        return jsonify({
            "mensagem": "Reunião salva com sucesso!",
            "meeting_id": meeting_id
        })
        
    except Exception as e:
        logger.error(f"💥 ERRO GERAL: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500
    
# ...existing code...
@app.route('/agenda/recent-changes')
@login_requerido
def get_recent_changes():
    """Retorna reuniões com mudanças recentes de status"""
    try:
        # Pega parâmetro de tempo (últimos 5 minutos por padrão)
        since = request.args.get('since')
        if not since:
            since = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Busca reuniões com respostas recentes
            cursor.execute('''
                SELECT 
                    r.id,
                    r.titulo,
                    r.convidado,
                    r.status_confirmacao,
                    cr.response_text,
                    cr.status as response_status,
                    cr.received_at,
                    cr.confidence
                FROM reunioes r
                INNER JOIN client_responses cr ON r.id = cr.meeting_id
                WHERE datetime(cr.received_at) >= datetime(?)
                ORDER BY cr.received_at DESC
            ''', (since,))
            
            changes = []
            for row in cursor.fetchall():
                changes.append({
                    'meeting_id': row[0],
                    'title': row[1],
                    'guest': row[2],
                    'current_status': row[3],
                    'response_text': row[4],
                    'response_status': row[5],
                    'received_at': row[6],
                    'confidence': row[7]
                })
            
            return jsonify({
                'success': True,
                'changes': changes,
                'count': len(changes),
                'since': since
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar mudanças: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ...existing code...
    
# ROTA PARA LIMPAR DUPLICATAS EXISTENTES (adicione também)
@app.route('/agenda/limpar-duplicatas', methods=['POST'])
@login_requerido
def limpar_duplicatas():
    """Remove duplicatas existentes baseado em título + convidado + data"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Busca duplicatas (mesmo título, convidado e data)
            cursor.execute('''
                SELECT id, titulo, convidado, data_hora, created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY UPPER(TRIM(titulo)), UPPER(TRIM(convidado)), DATE(data_hora), TIME(data_hora)
                           ORDER BY created_at DESC
                       ) as row_num
                FROM reunioes
            ''')
            
            todas_reunioes = cursor.fetchall()
            ids_para_remover = []
            
            for reuniao in todas_reunioes:
                if reuniao[5] > 1:  # row_num > 1 significa duplicata
                    ids_para_remover.append(reuniao[0])
            
            # Remove duplicatas e dados relacionados
            removidas = 0
            for meeting_id in ids_para_remover:
                cursor.execute('DELETE FROM whatsapp_logs WHERE meeting_id = ?', (meeting_id,))
                cursor.execute('DELETE FROM client_responses WHERE meeting_id = ?', (meeting_id,))
                cursor.execute('DELETE FROM reunioes WHERE id = ?', (meeting_id,))
                removidas += 1
            
            conn.commit()
            logger.info(f"Removidas {removidas} reuniões duplicadas")
            
            return jsonify({
                "success": True,
                "removidas": removidas,
                "message": f"{removidas} reuniões duplicadas removidas com sucesso"
            })
            
    except Exception as e:
        logger.error(f"Erro ao limpar duplicatas: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Testa processamento de webhook manualmente"""
    try:
        # Dados de teste simulando uma mensagem
        test_data = {
            "event": "messages.upsert",
            "instanceName": EVOLUTION_API_CONFIG["instance_name"],
            "data": {
                "key": {
                    "remoteJid": "5521982161008@s.whatsapp.net"
                },
                "message": {
                    "conversation": "sim, confirmo"
                }
            }
        }
        
        logger.info("🧪 Testando webhook com dados simulados")
        result = whatsapp_monitor.process_webhook_message(test_data)
        
        return jsonify({
            "success": True,
            "test_result": result,
            "monitoring_active": whatsapp_monitor.monitoring,
            "monitored_phones": list(whatsapp_monitor.monitored_phones)
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de webhook: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

# CLASSE AUTOMSGSENDER MELHORADA
class AutoMessageSender:
    """Classe para envio automático de mensagens em background - VERSÃO MELHORADA"""
    
    @staticmethod
    def send_confirmation_message_async(meeting_id: int, delay_seconds: int = 1):
        """Envia mensagem de confirmação de forma assíncrona com melhor tratamento de erros"""
        def _send_message():
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Aguarda antes de enviar
                    time.sleep(delay_seconds if attempt == 0 else retry_delay)
                    
                    logger.info(f"📤 Tentativa {attempt + 1}/{max_retries} - Enviando automático para reunião {meeting_id}")
                    
                    # Busca dados da reunião
                    with sqlite3.connect(DATABASE) as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
                        meeting = cursor.fetchone()
                        
                        if not meeting:
                            logger.error(f"Reunião {meeting_id} não encontrada")
                            return
                    
                    # Verifica se tem telefone
                    telefone_cliente = meeting[7] if len(meeting) > 7 else None
                    if not telefone_cliente:
                        logger.warning(f"Reunião {meeting_id} sem telefone")
                        AutoMessageSender._log_failed_attempt(meeting_id, "", "Telefone não informado", "no_phone")
                        return
                    
                    # Verifica conexão com timeout baixo
                    try:
                        logger.info(f"🔍 Verificando conexão WhatsApp (tentativa {attempt + 1})...")
                        connected, status = evolution_manager.check_connection_status()
                        
                        if not connected:
                            logger.warning(f"⚠️ WhatsApp não conectado (tentativa {attempt + 1}): {status}")
                            
                            # Se última tentativa, registra falha definitiva
                            if attempt == max_retries - 1:
                                AutoMessageSender._log_failed_attempt(
                                    meeting_id, telefone_cliente, 
                                    f"WhatsApp não conectado após {max_retries} tentativas: {status}", 
                                    "not_connected"
                                )
                                return
                            else:
                                # Tenta novamente
                                logger.info(f"🔄 Tentando novamente em {retry_delay}s...")
                                continue
                                
                    except Exception as conn_error:
                        logger.error(f"❌ Erro ao verificar conexão (tentativa {attempt + 1}): {conn_error}")
                        
                        if attempt == max_retries - 1:
                            AutoMessageSender._log_failed_attempt(
                                meeting_id, telefone_cliente, 
                                f"Erro na verificação de conexão: {conn_error}", 
                                "connection_check_error"
                            )
                            return
                        else:
                            continue
                    
                    # Prepara dados da mensagem
                    logger.info("📝 Preparando mensagem...")
                    meeting_data = {
                        'convidado': meeting[2],
                        'data_hora': meeting[3],
                        'assunto': meeting[4],
                        'link': meeting[5] or '',
                        'nome_cliente': meeting[6] or '',
                        'local_reuniao': meeting[8] if len(meeting) > 8 else ''
                    }
                    
                    # Carrega e formata template
                    template = MessageTemplateManager.load_template()
                    formatted_message = MessageTemplateManager.format_message(template, meeting_data)
                    formatted_message = f"{formatted_message}"
                    
                    # Normaliza telefone
                    normalized_phone = evolution_manager.normalize_phone_number(telefone_cliente)
                    logger.info(f"📱 Enviando para: {normalized_phone}")
                    
                    # ENVIA MENSAGEM
                    success, result = evolution_manager.send_message(telefone_cliente, formatted_message)
                    
                    # Registra log do resultado
                    log_whatsapp_message(
                        meeting_id=meeting_id,
                        phone=normalized_phone,
                        message=formatted_message,
                        status="success" if success else "failed",
                        error_message=None if success else result
                    )
                    
                    if success:
                        logger.info(f"✅ ENVIO AUTOMÁTICO BEM-SUCEDIDO! (tentativa {attempt + 1})")
                        
                        # Adiciona ao monitoramento para capturar resposta
                        whatsapp_monitor.add_phone_to_monitor(telefone_cliente, meeting_id)
                        
                        # Registra sucesso na base
                        AutoMessageSender._log_success(meeting_id, normalized_phone, formatted_message)
                        return
                    
                    else:
                        logger.error(f"❌ FALHA no envio (tentativa {attempt + 1}): {result}")
                        
                        # Se última tentativa, registra falha definitiva
                        if attempt == max_retries - 1:
                            AutoMessageSender._log_failed_attempt(
                                meeting_id, normalized_phone, result, "send_failed"
                            )
                            return
                        else:
                            # Aguarda antes de tentar novamente
                            logger.info(f"🔄 Tentando novamente em {retry_delay}s...")
                            continue
                            
                except Exception as e:
                    logger.error(f"💥 Erro interno na tentativa {attempt + 1}: {e}")
                    
                    if attempt == max_retries - 1:
                        AutoMessageSender._log_failed_attempt(
                            meeting_id, telefone_cliente, f"Erro interno: {str(e)}", "internal_error"
                        )
                        return
                    else:
                        continue
            
            logger.error(f"❌ FALHA DEFINITIVA após {max_retries} tentativas para reunião {meeting_id}")
        
        # Executa em thread separada para não bloquear resposta HTTP
        thread = threading.Thread(target=_send_message, daemon=True)
        thread.start()
        logger.info(f"🚀 Thread de envio automático iniciada para reunião {meeting_id}")
    
    @staticmethod
    def _log_success(meeting_id: int, phone: str, message: str):
        """Registra sucesso no envio automático"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO whatsapp_logs (meeting_id, phone, message, status, error_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (meeting_id, phone, message, "auto_success", None))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar sucesso: {e}")
    
    @staticmethod
    def _log_failed_attempt(meeting_id: int, phone: str, error_msg: str, error_type: str):
        """Registra falha no envio automático"""
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO whatsapp_logs (meeting_id, phone, message, status, error_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (meeting_id, phone, f"[AUTOMÁTICO] Falha: {error_type}", "auto_failed", error_msg))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar falha: {e}")

# FUNÇÕES DE VERIFICAÇÃO DE CONFLITO DE HORÁRIO
def verificar_conflito_horario(data_hora: str, meeting_id: int = None, tolerancia_minutos: int = 15) -> dict:
    """
    Verifica se existe conflito de horário com outras reuniões
    
    Args:
        data_hora: Data/hora da reunião no formato ISO
        meeting_id: ID da reunião atual (para ignorar na verificação de edição)
        tolerancia_minutos: Tolerância em minutos para considerar conflito
    
    Returns:
        dict: Dados da reunião em conflito ou None se não houver conflito
    """
    try:
        # Parse da data/hora da nova reunião
        nova_data = parser.parse(data_hora)
        
        # Calcula janela de conflito (tolerância antes e depois)
        inicio_janela = nova_data - timedelta(minutes=tolerancia_minutos)
        fim_janela = nova_data + timedelta(minutes=tolerancia_minutos)
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Query para buscar reuniões conflitantes
            if meeting_id:
                # Para edição: ignora a reunião atual
                cursor.execute('''
                    SELECT id, titulo, convidado, data_hora, nome_cliente
                    FROM reunioes 
                    WHERE id != ? 
                    AND datetime(data_hora) BETWEEN datetime(?) AND datetime(?)
                    ORDER BY data_hora
                ''', (meeting_id, inicio_janela.isoformat(), fim_janela.isoformat()))
            else:
                # Para nova reunião: verifica todos
                cursor.execute('''
                    SELECT id, titulo, convidado, data_hora, nome_cliente
                    FROM reunioes 
                    WHERE datetime(data_hora) BETWEEN datetime(?) AND datetime(?)
                    ORDER BY data_hora
                ''', (inicio_janela.isoformat(), fim_janela.isoformat()))
            
            reuniao_conflitante = cursor.fetchone()
            
            if reuniao_conflitante:
                # Calcula diferença em minutos
                data_existente = parser.parse(reuniao_conflitante[3])
                diferenca_minutos = abs((nova_data - data_existente).total_seconds() / 60)
                
                return {
                    "id": reuniao_conflitante[0],
                    "titulo": reuniao_conflitante[1],
                    "convidado": reuniao_conflitante[2],
                    "data_hora": reuniao_conflitante[3],
                    "nome_cliente": reuniao_conflitante[4] or "",
                    "diferenca_minutos": int(diferenca_minutos),
                    "tolerancia_aplicada": tolerancia_minutos
                }
            
            return None
            
    except Exception as e:
        logger.error(f"Erro ao verificar conflito de horário: {e}")
        return None

def formatar_conflito_para_usuario(conflito: dict) -> str:
    """Formata mensagem de conflito para exibição ao usuário"""
    if not conflito:
        return ""
    
    data_formatada = parser.parse(conflito["data_hora"]).strftime("%d/%m/%Y às %H:%M")
    diferenca = conflito["diferenca_minutos"]
    
    if diferenca == 0:
        tempo_desc = "no mesmo horário"
    elif diferenca <= 5:
        tempo_desc = f"{diferenca} minutos de diferença"
    else:
        tempo_desc = f"{diferenca} minutos de diferença"
    
    cliente_info = f" (Cliente: {conflito['nome_cliente']})" if conflito['nome_cliente'] else ""
    
    return f"'{conflito['titulo']}' com {conflito['convidado']} em {data_formatada} - {tempo_desc}{cliente_info}"

# ROTA PARA VERIFICAR CONFLITOS (AJAX)
@app.route('/agenda/verificar-conflito', methods=['POST'])
@login_requerido
def verificar_conflito_ajax():
    """Endpoint AJAX para verificar conflitos em tempo real"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        data_hora = dados.get('data_hora')
        meeting_id = dados.get('meeting_id')  # Para edição
        tolerancia = dados.get('tolerancia_minutos', 15)
        
        if not data_hora:
            return jsonify({"erro": "Data/hora não fornecida"}), 400
        
        conflito = verificar_conflito_horario(data_hora, meeting_id, tolerancia)
        
        if conflito:
            return jsonify({
                "tem_conflito": True,
                "conflito": conflito,
                "mensagem": formatar_conflito_para_usuario(conflito),
                "sugestoes": gerar_sugestoes_horario(data_hora, tolerancia)
            })
        else:
            return jsonify({
                "tem_conflito": False,
                "mensagem": "Horário disponível"
            })
        
    except Exception as e:
        logger.error(f"Erro ao verificar conflito via AJAX: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500
    
# ADICIONE esta rota no arquivo Python:
@app.route('/agenda/meeting/<int:meeting_id>')
@login_requerido
def get_meeting_details(meeting_id):
    """Retorna dados atualizados de uma reunião específica"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
            meeting = cursor.fetchone()
            
            if not meeting:
                return jsonify({'success': False, 'message': 'Reunião não encontrada'}), 404
            
            # Converte para formato esperado pelo frontend
            meeting_data = {
                'id': meeting[0],
                'title': meeting[1],
                'convidado': meeting[2],
                'datetime': meeting[3],
                'assunto': meeting[4],
                'link': meeting[5] or '',
                'client': meeting[6] or '',
                'phone': meeting[7] or '',
                'local': meeting[8] if len(meeting) > 8 else '',
                'status_confirmacao': meeting[9] if len(meeting) > 9 else 'pending'
            }
            
            return jsonify({
                'success': True,
                'meeting': meeting_data
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar reunião: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def gerar_sugestoes_horario(data_hora_original: str, tolerancia: int = 15) -> list:
    """Gera sugestões de horários alternativos"""
    try:
        data_original = parser.parse(data_hora_original)
        sugestoes = []
        
        # Gera sugestões: antes e depois do horário original
        intervalos = [-60, -30, 30, 60, 90, 120]  # minutos
        
        for intervalo in intervalos:
            nova_data = data_original + timedelta(minutes=intervalo)
            
            # Verifica se o horário sugerido também tem conflito
            conflito_sugestao = verificar_conflito_horario(nova_data.isoformat(), tolerancia=tolerancia)
            
            if not conflito_sugestao:
                sugestoes.append({
                    "data_hora": nova_data.isoformat(),
                    "data_formatada": nova_data.strftime("%d/%m/%Y"),
                    "hora_formatada": nova_data.strftime("%H:%M"),
                    "diferenca_original": f"{abs(intervalo)} min {'antes' if intervalo < 0 else 'depois'}"
                })
                
                # Limita a 3 sugestões
                if len(sugestoes) >= 3:
                    break
        
        return sugestoes
        
    except Exception as e:
        logger.error(f"Erro ao gerar sugestões: {e}")
        return []

    
@app.route('/whatsapp/auto-send-status/<int:meeting_id>')
@login_requerido
def get_auto_send_status(meeting_id):
    """Verifica status do envio automático de uma reunião"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, error_message, sent_at 
                FROM whatsapp_logs 
                WHERE meeting_id = ? AND (status LIKE 'auto_%' OR message LIKE '[AUTOMÁTICO]%')
                ORDER BY sent_at DESC 
                LIMIT 1
            ''', (meeting_id,))
            
            result = cursor.fetchone()
            
            if result:
                status, error_msg, sent_at = result
                return jsonify({
                    "success": True,
                    "auto_send_status": status,
                    "error_message": error_msg,
                    "sent_at": sent_at,
                    "is_success": status == "auto_success"
                })
            else:
                return jsonify({
                    "success": True,
                    "auto_send_status": "not_attempted",
                    "message": "Nenhum envio automático encontrado"
                })
                
    except Exception as e:
        logger.error(f"Erro ao verificar status do envio automático: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500


@app.route('/agenda/dados')
@login_requerido
def dados_reunioes():
    try:
        reunioes = get_reunioes()
        lista = []
        
        for r in reunioes:
            # Ordem garantida pelo SELECT explícito:
            # 0=id, 1=titulo, 2=convidado, 3=data_hora, 4=assunto,
            # 5=link, 6=nome_cliente, 7=telefone_cliente, 
            # 8=local_reuniao, 9=status_confirmacao, 10=numero_pessoas
            
            lista.append({
                "id": r[0],
                "title": r[1],
                "convidado": r[2],
                "datetime": r[3],
                "assunto": r[4],
                "link": r[5] or "",
                "client": r[6] or "",
                "phone": r[7] or "",
                "local": r[8] or "",
                "status_confirmacao": r[9] if len(r) > 9 else "pending",
                "numero_pessoas": r[10] if len(r) > 10 else None  # ✅ ÍNDICE 10 CORRETO
            })
        
        return jsonify(lista)
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        return jsonify({"erro": f"Erro ao buscar dados: {str(e)}"}), 500

@app.route('/agenda/excluir/<int:id>', methods=['DELETE'])
@login_requerido
def excluir_reuniao(id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM reunioes WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({'erro': 'Reunião não encontrada'}), 404
            
            cursor.execute('DELETE FROM reunioes WHERE id = ?', (id,))
            cursor.execute('DELETE FROM client_responses WHERE meeting_id = ?', (id,))
            conn.commit()
            logger.info(f"Reunião {id} excluída")
        return jsonify({'mensagem': 'Reunião excluída com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao excluir reunião: {e}")
        return jsonify({'erro': f'Erro ao excluir reunião: {str(e)}'}), 500

@app.route('/agenda/editar/<int:id>', methods=['PUT'])
@login_requerido
def editar_reuniao(id):
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados não fornecidos"}), 400
            
        titulo = dados.get('titulo')
        convidado = dados.get('convidado')
        data_hora = dados.get('data_hora')
        assunto = dados.get('assunto')
        link = dados.get('link', '')
        nome_cliente = dados.get('nome_cliente', '')
        telefone_cliente = dados.get('telefone_cliente', '')
        local_reuniao = dados.get('local_reuniao', '')

        # 🆕 ADICIONE VALIDAÇÃO DO NUMERO_PESSOAS
        numero_pessoas = dados.get('numero_pessoas')
        if numero_pessoas:
            try:
                numero_pessoas = int(numero_pessoas)
                if numero_pessoas < 1 or numero_pessoas > 100:
                    numero_pessoas = None
            except (ValueError, TypeError):
                numero_pessoas = None

        if not all([titulo, convidado, data_hora, assunto]):
            return jsonify({"erro": "Campos obrigatórios não preenchidos"}), 400

        try:
            parser.parse(data_hora)
        except Exception:
            return jsonify({"erro": "Data inválida"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM reunioes WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({'erro': 'Reunião não encontrada'}), 404
            
            # 🆕 ADICIONE numero_pessoas NO UPDATE
            cursor.execute('''
                UPDATE reunioes
                SET titulo = ?, convidado = ?, data_hora = ?, assunto = ?, link = ?, nome_cliente = ?, telefone_cliente = ?, local_reuniao = ?, numero_pessoas = ?
                WHERE id = ?
            ''', (titulo, convidado, data_hora, assunto, link, nome_cliente, telefone_cliente, local_reuniao, numero_pessoas, id))
            conn.commit()
            logger.info(f"Reunião {id} editada")

        return jsonify({'mensagem': 'Reunião atualizada com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao editar reunião: {e}")
        return jsonify({'erro': f'Erro ao editar reunião: {str(e)}'}), 500

# ===============================
# === WEBHOOK EVOLUTION API =====
# ===============================
@app.route('/webhook/evolution', methods=['POST'])
def evolution_webhook():
    """WEBHOOK COMPLETO — Valida, processa e registra eventos da Evolution API"""
    try:

        expected_key = os.getenv("EVOLUTION_API_KEY", EVOLUTION_API_CONFIG.get("api_key", ""))


        # =============================
        # 2️⃣ Leitura e validação do JSON
        # =============================
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.error(f"💥 Erro ao decodificar JSON: {e}")
            return jsonify({"error": "Invalid JSON"}), 400

        if not data:
            logger.warning("⚠️ Webhook sem corpo JSON válido")
            return jsonify({"error": "No JSON data"}), 400

        # =============================
        # 3️⃣ Log e auditoria do webhook
        # =============================
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO webhook_incoming_logs (event, instance, raw_payload)
                    VALUES (?, ?, ?)
                """, (
                    data.get("event", ""),
                    data.get("instance", data.get("instanceName", "")),
                    json.dumps(data)
                ))
                conn.commit()
            logger.info("💾 Payload do webhook salvo com sucesso")
        except Exception as log_err:
            logger.warning(f"⚠️ Falha ao salvar log do webhook: {log_err}")

        logger.info("📥 WEBHOOK RECEBIDO:")
        logger.info(f"   Event: {data.get('event', 'N/A')}")
        logger.info(f"   Instance: {data.get('instance', 'N/A')}")
        logger.info(f"   Data keys: {list(data.keys())}")

        # =============================
        # 4️⃣ Ativação automática do monitoramento
        # =============================
        if not whatsapp_monitor.monitoring:
            logger.info("🔄 Ativando monitoramento automaticamente...")
            whatsapp_monitor.start_monitoring()

        # =============================
        # 5️⃣ Validação da instância
        # =============================
        instance_name = data.get("instance") or data.get("instanceName")
        expected_instance = getattr(evolution_manager, "instance_name", None)
        if expected_instance and instance_name != expected_instance:
            logger.warning(f"⚠️ Instância incorreta: esperado '{expected_instance}', recebido '{instance_name}'")
            return jsonify({"status": "ignored", "reason": "wrong_instance"}), 200

        # =============================
        # 6️⃣ Filtro de eventos válidos
        # =============================
        event = str(data.get("event", "")).lower()
        VALID_EVENTS = {
            "messages.upsert", "message.upsert", "messages_upsert", "message",
            "messages", "send.message", "receive.message", "messages.set", "messaging-history.set"
        }
        if event and not any(valid in event for valid in VALID_EVENTS):
            logger.info(f"⚠️ Evento ignorado (não é mensagem): {event}")
            return jsonify({"status": "ignored", "reason": "not_message_event"}), 200

        # =============================
        # 7️⃣ Extração dos dados da mensagem
        # =============================
        try:
            message_data = None
            if "data" in data:
                if isinstance(data["data"], list) and data["data"]:
                    message_data = data["data"][0]
                elif isinstance(data["data"], dict):
                    message_data = data["data"]
            elif "key" in data and "message" in data:
                message_data = data

            if not message_data:
                raise ValueError("Estrutura de dados não reconhecida")

            logger.info("📦 Dados da mensagem extraídos com sucesso")
        except Exception as extract_error:
            logger.error(f"💥 Erro ao extrair dados da mensagem: {extract_error}")
            return jsonify({"status": "error", "message": str(extract_error)}), 200

        # =============================
        # 8️⃣ Processamento da mensagem
        # =============================
        logger.info("🔍 Processando mensagem recebida...")
        try:
            result = whatsapp_monitor.process_webhook_message(message_data)
        except Exception as proc_err:
            logger.warning(f"⚠️ Erro durante o processamento: {proc_err}")
            result = False

        # =============================
        # 9️⃣ Confirmação automática de reuniões
        # =============================
        try:
            message_text = ""
            sender_number = ""

            # Extrai texto da mensagem
            if "message" in message_data:
                message_text = (
                    message_data.get("message", {}).get("conversation")
                    or message_data.get("message", {}).get("extendedTextMessage", {}).get("text", "")
                    or ""
                )

            # Extrai número do remetente
            if "key" in message_data:
                sender_number = (
                    message_data.get("key", {}).get("remoteJid", "")
                    .split("@")[0]
                    .replace(" ", "")
                    .replace("+", "")
                )

            logger.info(f"💬 Mensagem recebida de {sender_number}: {message_text}")

            palavras_confirmacao = ["confirmado", "confirmada", "sim", "ok", "pode confirmar"]

            if sender_number and any(p in message_text.lower() for p in palavras_confirmacao):
                logger.info(f"✅ Confirmação automática detectada para {sender_number}")

                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id FROM reunioes 
                        WHERE telefone_cliente LIKE ? 
                        ORDER BY id DESC LIMIT 1
                    """, (f"%{sender_number[-8:]}%",))
                    row = cursor.fetchone()

                    if row:
                        meeting_id = row[0]
                        cursor.execute("""
                            UPDATE reunioes
                            SET status_confirmacao = 'confirmada'
                            WHERE id = ?
                        """, (meeting_id,))
                        cursor.execute("""
                            INSERT INTO client_responses 
                                (meeting_id, response_text, status, confidence, analysis_data, received_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            meeting_id,
                            "[CONFIRMAÇÃO AUTOMÁTICA] Status alterado para: confirmed",
                            "confirmed",
                            1.0,
                            json.dumps({
                                "manual": False,
                                "fonte": "webhook",
                                "numero": sender_number
                            }),
                            datetime.now().isoformat()
                        ))
                        conn.commit()
                        logger.info(f"💾 Reunião {meeting_id} marcada como CONFIRMADA automaticamente")
                    else:
                        logger.warning(f"⚠️ Nenhuma reunião encontrada para o número {sender_number}")

        except Exception as auto_err:
            logger.error(f"💥 Erro na confirmação automática: {auto_err}")

        # =============================
        # 🔚 10️⃣ Retorno final
        # =============================
        return jsonify({
            "status": "success",
            "processed": bool(result),
            "message": "Webhook received and processed",
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"💥 Erro crítico no webhook: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "processed": False,
            "timestamp": datetime.now().isoformat()
        }), 200

    
# ===============================
# === ROTAS EVOLUTION API =======
# ===============================
@app.route('/whatsapp/connect-existing', methods=['POST'])
@login_requerido
def connect_existing_instance():
    """CORRIGIDO: Conecta com instância existente SEM criar nova"""
    try:
        logger.info("🔗 Conectando com instância existente...")
        
        # Usa o método corrigido
        success, message = evolution_manager.connect_existing_instance()
        
        if success:
            logger.info("✅ Conectado com instância existente")
            return jsonify({
                "success": True,
                "message": message,
                "instance_name": evolution_manager.instance_name,
                "status": "connected"
            })
        else:
            logger.warning(f"⚠️ Falha na conexão: {message}")
            return jsonify({
                "success": False,
                "message": message,
                "instance_name": evolution_manager.instance_name,
                "status": "disconnected"
            })
            
    except Exception as e:
        logger.error(f"💥 Erro ao conectar: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/whatsapp/generate-qr', methods=['POST'])
@login_requerido
def generate_whatsapp_qr():
    """CORRIGIDO: Gera QR Code de instância existente"""
    try:
        logger.info("📱 Gerando QR Code da instância existente...")
        
        # Primeiro verifica se instância existe
        instance_ok, instance_msg = evolution_manager.check_existing_instance()
        
        if not instance_ok and "não existe" in instance_msg.lower():
            return jsonify({
                "success": False,
                "message": f"❌ INSTÂNCIA NÃO EXISTE: Você precisa criar a instância '{evolution_manager.instance_name}' primeiro no Evolution Manager (porta 8090).",
                "create_instructions": [
                    "1. Acesse http://82.25.69.24:8090",
                    f"2. Crie uma instância com nome: {evolution_manager.instance_name}",
                    "3. Configure o webhook se necessário",
                    "4. Volte aqui e tente novamente"
                ]
            }), 404
        
        # Tenta obter QR Code
        qr_code = evolution_manager.get_qr_code()
        
        if qr_code:
            logger.info("✅ QR Code obtido com sucesso")
            return jsonify({
                "success": True,
                "qr_code": qr_code,
                "message": "QR Code gerado com sucesso",
                "instance_name": evolution_manager.instance_name,
                "instructions": "Escaneie o QR Code com seu WhatsApp"
            })
        else:
            # Se não conseguiu QR, pode já estar conectada
            if instance_ok:
                return jsonify({
                    "success": False,
                    "message": "Instância já está conectada - QR Code não é necessário",
                    "already_connected": True
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Não foi possível obter QR Code. Verifique se a instância está criada no Evolution Manager."
                }), 500
            
    except Exception as e:
        logger.error(f"Erro ao gerar QR Code: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/whatsapp/test-send', methods=['POST'])
@login_requerido
def test_send_message():
    """NOVO: Rota para testar envio de mensagem"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        phone = dados.get('phone', '21982161008')  # Seu número como padrão
        message = dados.get('message', '🧪 TESTE: Sistema de reuniões funcionando!')
        
        logger.info(f"🧪 Testando envio para {phone}")
        
        # Verifica conexão primeiro
        connected, status = evolution_manager.check_connection_status()
        if not connected:
            return jsonify({
                "success": False,
                "message": f"Instância não conectada: {status}",
                "action_needed": "Conecte primeiro via QR Code"
            })
        
        # Envia mensagem teste
        success, result = evolution_manager.send_message(phone, message)
        
        return jsonify({
            "success": success,
            "message": result,
            "phone_used": evolution_manager.normalize_phone_number(phone),
            "instance": evolution_manager.instance_name
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de envio: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/status')
def whatsapp_status():
    """CORRIGIDO: Status da conexão sem criar instância"""
    try:
        # Verifica instância existente
        instance_ok, instance_msg = evolution_manager.check_existing_instance()
        
        return jsonify({
            "connected": instance_ok,
            "status_message": instance_msg,
            "instance_name": evolution_manager.instance_name,
            "instance_exists": "não existe" not in instance_msg.lower(),
            "monitoring_active": whatsapp_monitor.monitoring,
            "api_url": evolution_manager.base_url,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            "connected": False,
            "status_message": f"Erro ao verificar status: {str(e)}",
            "instance_name": evolution_manager.instance_name,
            "instance_exists": False,
            "monitoring_active": False,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/whatsapp/restart', methods=['POST'])
@login_requerido
def restart_whatsapp():
    """Reinicia instância existente (NÃO CRIA NOVA)"""
    try:
        logger.info("Reiniciando instância existente...")
        
        # Primeiro verifica se a instância existe
        instance_ok, instance_msg = evolution_manager.check_existing_instance()
        
        if not instance_ok and "não existe" in instance_msg.lower():
            return jsonify({
                "success": False,
                "message": f"Instância '{evolution_manager.instance_name}' não existe no Evolution Manager. Crie-a manualmente primeiro."
            }), 404
        
        # Tenta reiniciar a instância existente
        success, message = evolution_manager.restart_instance()
        
        if success:
            logger.info("Instância existente reiniciada com sucesso")
        else:
            logger.error(f"Erro ao reiniciar instância existente: {message}")
        
        return jsonify({
            "success": success,
            "message": message,
            "instance_name": evolution_manager.instance_name
        })
        
    except Exception as e:
        logger.error(f"Erro ao reiniciar WhatsApp: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/whatsapp/force-status-check', methods=['POST'])
@login_requerido
def force_status_check():
    """Força verificação de status da instância existente"""
    try:
        logger.info("Forçando verificação de status da instância existente...")
        
        # Verifica instância existente
        instance_ok, instance_msg = evolution_manager.check_existing_instance()
        
        # Verifica conexão específica
        connected, conn_status = evolution_manager.check_connection_status()
        
        return jsonify({
            "success": True,
            "instance_exists": instance_ok or "não existe" not in instance_msg.lower(),
            "instance_message": instance_msg,
            "connected": connected,
            "connection_status": conn_status,
            "api_key_used": evolution_manager.api_key[:10] + "...",
            "instance_name": evolution_manager.instance_name
        })
        
    except Exception as e:
        logger.error(f"Erro na verificação forçada: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        })
    
@app.route('/whatsapp/send-message', methods=['POST'])
@login_requerido
def send_whatsapp_message():
    """Envia mensagem via rota"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        meeting_id = dados.get('meeting_id')
        phone = dados.get('phone')
        message = dados.get('message')
        
        if not all([meeting_id, phone, message]):
            return jsonify({
                "success": False, 
                "message": "Dados obrigatórios não fornecidos (meeting_id, phone, message)"
            }), 400
        
        # Verifica se reunião existe
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
            meeting = cursor.fetchone()
            
            if not meeting:
                return jsonify({
                    "success": False,
                    "message": "Reunião não encontrada"
                }), 404
        
        # Normaliza telefone
        normalized_phone = evolution_manager.normalize_phone_number(phone)
        logger.info(f"Enviando mensagem para reunião {meeting_id}, telefone: {normalized_phone}")
        
        # USA O MÉTODO DA CLASSE EVOLUTION_MANAGER
        success, result_message = evolution_manager.send_message(phone, message)
        
        # Registra log
        log_whatsapp_message(
            meeting_id=meeting_id,
            phone=normalized_phone,
            message=message,
            status="success" if success else "error",
            error_message=None if success else result_message
        )
        
        # Se envio foi bem-sucedido, adiciona ao monitoramento
        if success:
            whatsapp_monitor.add_phone_to_monitor(phone, meeting_id)
        
        return jsonify({
            "success": success,
            "message": result_message,
            "phone_used": normalized_phone
        })
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/whatsapp/send-formatted-message', methods=['POST'])
@login_requerido
def send_formatted_message():
    """CORRIGIDO: Envia mensagem formatada usando instância existente"""
    try:
        dados = request.get_json()
        meeting_id = dados.get('meeting_id')
        
        if not meeting_id:
            return jsonify({
                "success": False,
                "message": "ID da reunião não fornecido"
            }), 400
        
        # Busca dados da reunião
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
            meeting = cursor.fetchone()
            
            if not meeting:
                return jsonify({
                    "success": False,
                    "message": "Reunião não encontrada"
                }), 404
        
        # Prepara dados
        meeting_data = {
            'convidado': meeting[2],
            'data_hora': meeting[3],
            'assunto': meeting[4],
            'link': meeting[5] or '',
            'nome_cliente': meeting[6] or '',
            'telefone_cliente': meeting[7] or '',
            'local_reuniao': meeting[8] if len(meeting) > 8 else ''
        }
        
        if not meeting_data['telefone_cliente']:
            return jsonify({
                "success": False,
                "message": "Telefone do cliente não informado"
            }), 400
        
        # Verifica conexão
        connected, status = evolution_manager.check_connection_status()
        if not connected:
            return jsonify({
                "success": False,
                "message": f"WhatsApp não conectado: {status}",
                "action_needed": "Conecte primeiro via QR Code"
            })
        
        # Formata mensagem
        template = MessageTemplateManager.load_template()
        formatted_message = MessageTemplateManager.format_message(template, meeting_data)
        
        # Envia mensagem
        success, result_message = evolution_manager.send_message(
            meeting_data['telefone_cliente'], 
            formatted_message
        )
        
        # Registra log
        log_whatsapp_message(
            meeting_id=meeting_id,
            phone=evolution_manager.normalize_phone_number(meeting_data['telefone_cliente']),
            message=formatted_message,
            status="success" if success else "error",
            error_message=None if success else result_message
        )
        
        # Adiciona ao monitoramento se sucesso
        if success:
            whatsapp_monitor.add_phone_to_monitor(meeting_data['telefone_cliente'], meeting_id)
        
        return jsonify({
            "success": success,
            "message": result_message,
            "phone_used": evolution_manager.normalize_phone_number(meeting_data['telefone_cliente']),
            "formatted_message": formatted_message[:100] + "..." if len(formatted_message) > 100 else formatted_message
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem formatada: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/add-to-monitoring', methods=['POST'])
@login_requerido
def add_phone_to_monitoring():
    """Adiciona telefone ao monitoramento de respostas"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        meeting_id = dados.get('meeting_id')
        phone = dados.get('phone')
        
        if not meeting_id or not phone:
            return jsonify({
                "success": False,
                "message": "meeting_id e phone são obrigatórios"
            }), 400
        
        # Normaliza telefone
        normalized_phone = evolution_manager.normalize_phone_number(phone)
        
        # Adiciona ao monitoramento
        whatsapp_monitor.add_phone_to_monitor(normalized_phone, meeting_id)
        
        logger.info(f"📱 Telefone {normalized_phone} adicionado ao monitoramento (reunião {meeting_id})")
        
        return jsonify({
            "success": True,
            "message": f"Telefone adicionado ao monitoramento",
            "normalized_phone": normalized_phone,
            "meeting_id": meeting_id,
            "monitored_phones": len(whatsapp_monitor.monitored_phones)
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar ao monitoramento: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/force-monitor-all', methods=['POST'])
def force_monitor_all_public():
    """
    Força monitoramento (PÚBLICO - sem login)
    CORREÇÃO: Remove @login_requerido para funcionar no test_webhook.py
    """
    try:
        logger.info("🔄 Forçando monitoramento de todos os telefones...")
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, titulo, telefone_cliente 
                FROM reunioes 
                WHERE telefone_cliente IS NOT NULL 
                AND telefone_cliente != ''
                AND datetime(data_hora) >= datetime('now', '-7 days')
                AND datetime(data_hora) <= datetime('now', '+30 days')
            ''')
            
            meetings = cursor.fetchall()
            monitored_count = 0
            added_phones = []
            
            for meeting_id, titulo, telefone in meetings:
                try:
                    normalized_phone = evolution_manager.normalize_phone_number(telefone)
                    whatsapp_monitor.add_phone_to_monitor(normalized_phone, meeting_id)
                    
                    added_phones.append({
                        "meeting_id": meeting_id,
                        "titulo": titulo,
                        "phone": normalized_phone
                    })
                    
                    logger.info(f"📱 Monitorando: {titulo[:30]}... - {normalized_phone}")
                    monitored_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao adicionar {telefone}: {e}")
        
        # Inicia monitoramento se não estiver ativo
        if not whatsapp_monitor.monitoring:
            whatsapp_monitor.start_monitoring()
            logger.info("🚀 Monitoramento ativado")
        
        logger.info(f"✅ Total monitorado: {len(whatsapp_monitor.monitored_phones)}")
        
        return jsonify({
            "success": True,
            "monitored_count": monitored_count,
            "total_monitored": len(whatsapp_monitor.monitored_phones),
            "added_phones": added_phones,
            "monitoring_active": whatsapp_monitor.monitoring
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao forçar monitoramento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 200  # Retorna 200 mesmo com erro
    
@app.route('/whatsapp/simulate-responses', methods=['POST'])
@login_requerido
def simulate_responses():
    """Simula respostas para reuniões que já receberam 'sim'"""
    try:
        # IDs das reuniões que você respondeu "sim"
        confirmed_meetings = [
            (79, "sim"),  # Teste 5000 
            (77, "sim")   # Isabelle
        ]
        
        for meeting_id, response_text in confirmed_meetings:
            # Verifica se já tem resposta
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM client_responses WHERE meeting_id = ?', (meeting_id,))
                existing_count = cursor.fetchone()[0]
                
                if existing_count == 0:
                    # Analisa resposta
                    analysis = ResponseAnalyzer.analyze_response(response_text)
                    
                    # Salva resposta
                    save_client_response(
                        meeting_id=meeting_id,
                        response_text=response_text,
                        status=analysis['status'],
                        confidence=analysis['confidence'],
                        analysis_data=json.dumps(analysis),
                        received_at=datetime.now().isoformat()
                    )
                    
                    # Atualiza status
                    update_meeting_status(meeting_id, analysis['status'])
                    
                    logger.info(f"✅ Resposta simulada para reunião {meeting_id}: {analysis['status']}")
        
        return jsonify({
            "success": True,
            "simulated_count": len(confirmed_meetings),
            "message": "Respostas simuladas com sucesso"
        })
        
    except Exception as e:
        logger.error(f"Erro ao simular respostas: {e}")
        return jsonify({"success": False, "error": str(e)})
# ===============================
# === ROTAS DE TEMPLATES ========
# ===============================
@app.route('/whatsapp/template', methods=['GET'])
@login_requerido
def get_message_template():
    """Retorna template atual"""
    try:
        template = MessageTemplateManager.load_template()
        return jsonify({
            "success": True,
            "template": template
        })
    except Exception as e:
        logger.error(f"Erro ao carregar template: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
#===================================
# Adicione estas funções que estão faltando:
@app.route('/whatsapp/template', methods=['POST'])
@login_requerido
def save_message_template():
    """Salva template de mensagem"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        template = dados.get('template')
        if not template:
            return jsonify({"success": False, "message": "Template não fornecido"}), 400
        
        success = MessageTemplateManager.save_template(template)
        
        return jsonify({
            "success": success,
            "message": "Template salvo com sucesso!" if success else "Erro ao salvar template"
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar template: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
def send_birthday_whatsapp_message(phone, message):
    """VERSÃO CORRIGIDA - Usa o mesmo padrão do manager principal"""
    try:
        logger.info(f"🎂 ENVIANDO ANIVERSÁRIO para {phone}")
        
        # SOLUÇÃO: Usa o manager global que já tem a lógica correta
        success, response = evolution_manager.send_message(phone, message)
        
        logger.info(f"🎂 Resultado aniversário: success={success}, response='{response}'")
        
        return success, response
        
    except Exception as e:
        logger.error(f"💥 Erro no envio de aniversário: {e}")
        return False, str(e)
# ===============================
# === ROTAS DE MONITORAMENTO ====
# ===============================
@app.route('/whatsapp/debug-monitoring')
@login_requerido
def debug_monitoring():
    """Debug do estado atual do monitoramento"""
    try:
        return jsonify({
            "success": True,
            "monitoring_active": whatsapp_monitor.monitoring,
            "monitored_phones": list(whatsapp_monitor.monitored_phones),
            "monitored_count": len(whatsapp_monitor.monitored_phones),
            "evolution_connected": evolution_manager.connected,
            "webhook_url": EVOLUTION_API_CONFIG['webhook_url']
        })
    except Exception as e:
        logger.error(f"Erro no debug: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/stop-monitoring', methods=['POST'])
@login_requerido
def stop_whatsapp_monitoring():
    """Para monitoramento de respostas"""
    try:
        whatsapp_monitor.stop_monitoring()
        return jsonify({
            "success": True,
            "message": "Monitoramento parado com sucesso"
        })
    except Exception as e:
        logger.error(f"Erro ao parar monitoramento: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/monitoring-status')
def get_monitoring_status_public():
    """
    Status do monitoramento (PÚBLICO - sem login)
    CORREÇÃO: Remove @login_requerido para funcionar no test_webhook.py
    """
    try:
        # Busca telefones sendo monitorados
        monitored_phones = list(whatsapp_monitor.monitored_phones)
        
        # Busca reuniões ativas que tem telefone
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM reunioes 
                WHERE telefone_cliente IS NOT NULL 
                AND telefone_cliente != ''
                AND datetime(data_hora) >= datetime('now')
            ''')
            meetings_with_phone = cursor.fetchone()[0]
            
            # Busca respostas recentes (últimas 24h)
            cursor.execute('''
                SELECT COUNT(*) FROM client_responses 
                WHERE datetime(received_at) >= datetime('now', '-1 day')
            ''')
            recent_responses = cursor.fetchone()[0]
        
        return jsonify({
            "success": True,
            "monitoring": whatsapp_monitor.monitoring,
            "monitored_phones": len(monitored_phones),
            "phones_list": [{"phone": p[0], "meeting_id": p[1]} for p in monitored_phones],
            "meetings_with_phone": meetings_with_phone,
            "recent_responses_24h": recent_responses,
            "whatsapp_connected": evolution_manager.connected,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status do monitoramento: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "monitoring": False,
            "monitored_phones": 0
        }), 200  # Retorna 200 mesmo com erro para o teste não falhar

# ===============================
# === ROTAS DE RESPOSTAS ========
# ===============================
@app.route('/agenda/responses/<int:meeting_id>')
@login_requerido
def get_meeting_responses(meeting_id):
    """Obtém respostas de uma reunião específica"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cr.*, r.titulo, r.convidado
                FROM client_responses cr
                LEFT JOIN reunioes r ON cr.meeting_id = r.id
                WHERE cr.meeting_id = ?
                ORDER BY cr.received_at DESC
            ''', (meeting_id,))
            
            responses = cursor.fetchall()
            
            response_list = []
            for resp in responses:
                response_list.append({
                    "id": resp[0],
                    "response_text": resp[2],
                    "status": resp[3],
                    "confidence": resp[4],
                    "analysis_data": json.loads(resp[5]) if resp[5] else {},
                    "received_at": resp[6],
                    "processed_at": resp[7],
                    "meeting_title": resp[8] if len(resp) > 8 else None,
                    "meeting_guest": resp[9] if len(resp) > 9 else None
                })
            
            return jsonify({
                "success": True,
                "responses": response_list
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar respostas: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/agenda/manual-confirmation/<int:meeting_id>', methods=['POST'])
@login_requerido
def manual_confirmation(meeting_id):
    """Permite confirmação manual da reunião"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        status = dados.get('status')  # 'confirmed', 'declined', 'pending'
        
        if status not in ['confirmed', 'declined', 'pending']:
            return jsonify({
                "success": False,
                "message": "Status inválido"
            }), 400
        
        # Atualiza status da reunião
        update_meeting_status(meeting_id, status)
        
        # Registra como confirmação manual
        save_client_response(
            meeting_id=meeting_id,
            response_text=f"[CONFIRMAÇÃO MANUAL] Status alterado para: {status}",
            status=status,
            confidence=1.0,
            analysis_data=json.dumps({"manual": True}),
            received_at=datetime.now().isoformat()
        )
        
        return jsonify({
            "success": True,
            "message": f"Status da reunião atualizado para: {status}"
        })
        
    except Exception as e:
        logger.error(f"Erro na confirmação manual: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@app.route('/test-auto-send-now', methods=['POST'])
@login_requerido
def test_auto_send_now():
    """Teste rápido do envio automático"""
    try:
        # Use seu número real aqui
        test_phone = "21982161008"  # Seu número da imagem
        test_message = "🧪 TESTE DE ENVIO AUTOMÁTICO - Se você recebeu esta mensagem, o sistema está funcionando!"
        
        logger.info("🧪 INICIANDO TESTE DE ENVIO AUTOMÁTICO")
        
        # Testa o envio
        success, result = evolution_manager.send_message(test_phone, test_message)
        
        return jsonify({
            "success": success,
            "message": result,
            "phone_tested": test_phone,
            "api_key_used": evolution_manager.api_key[:8] + "...",
            "instance": evolution_manager.instance_name
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
# =============================
# === TRATAMENTO DE ERROS ====
# =============================
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"Página não encontrada: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Erro interno: {e}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    logger.error(f"Acesso proibido: {request.url}")
    return render_template('403.html'), 403

# ===============================
# === ROTAS ADICIONAIS ==========
# ===============================
@app.route('/whatsapp/preview-message/<int:meeting_id>')
@login_requerido
def preview_message(meeting_id):
    """Preview da mensagem formatada"""
    try:
        # Busca dados da reunião
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reunioes WHERE id = ?', (meeting_id,))
            meeting = cursor.fetchone()
            
            if not meeting:
                return jsonify({
                    "success": False,
                    "message": "Reunião não encontrada"
                }), 404
        
        # Converte para dicionário
        meeting_data = {
            'convidado': meeting[2],
            'data_hora': meeting[3],
            'assunto': meeting[4],
            'link': meeting[5] or '',
            'nome_cliente': meeting[6] or '',
            'local_reuniao': meeting[8] if len(meeting) > 8 else ''
        }
        
        # Formata mensagem
        template = MessageTemplateManager.load_template()
        formatted_message = MessageTemplateManager.format_message(template, meeting_data)
        
        return jsonify({
            "success": True,
            "preview": formatted_message,
            "meeting_data": meeting_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar preview: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/logs')
@login_requerido
def get_whatsapp_logs():
    """Retorna logs de mensagens enviadas"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT wl.*, r.titulo, r.convidado 
                FROM whatsapp_logs wl
                LEFT JOIN reunioes r ON wl.meeting_id = r.id
                ORDER BY wl.sent_at DESC
                LIMIT 100
            ''')
            logs = cursor.fetchall()
            
            log_list = []
            for log in logs:
                log_list.append({
                    "id": log[0],
                    "meeting_id": log[1],
                    "phone": log[2],
                    "status": log[4],
                    "sent_at": log[5],
                    "error_message": log[6],
                    "meeting_title": log[7] if len(log) > 7 else None,
                    "meeting_guest": log[8] if len(log) > 8 else None
                })
            
            return jsonify({
                "success": True,
                "logs": log_list
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/test-phone', methods=['POST'])
@login_requerido
def test_phone_format():
    """Testa formatação de número de telefone"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        phone = dados.get('phone')
        if not phone:
            return jsonify({
                "success": False,
                "message": "Número de telefone não fornecido"
            }), 400
        
        normalized = evolution_manager.normalize_phone_number(phone)
        
        return jsonify({
            "success": True,
            "original": phone,
            "normalized": normalized,
            "whatsapp_id": normalized
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar telefone: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/instance-info')
@login_requerido
def get_instance_info():
    """Obtém informações da instância"""
    try:
        user_info = evolution_manager.get_user_info()
        success, status_info = evolution_manager.get_instance_status()
        
        return jsonify({
            "success": True,
            "instance_name": evolution_manager.instance_name,
            "user_info": user_info,
            "status_info": status_info if success else {},
            "connected": evolution_manager.connected
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter info da instância: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/whatsapp/delete-instance', methods=['DELETE'])
@login_requerido
def delete_whatsapp_instance():
    """Deleta instância WhatsApp"""
    try:
        success, message = evolution_manager.delete_instance()
        if success:
            evolution_manager.connected = False
            
        return jsonify({
            "success": success,
            "message": message
        })
    except Exception as e:
        logger.error(f"Erro ao deletar instância: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/agenda/confirmation-status')
@login_requerido
def get_confirmation_status():
    """Retorna status de confirmação de todas as reuniões"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, titulo, convidado, data_hora, status_confirmacao,
                       (SELECT COUNT(*) FROM client_responses WHERE meeting_id = reunioes.id) as response_count
                FROM reunioes 
                WHERE datetime(data_hora) >= datetime('now')
                ORDER BY data_hora
            ''')
            
            meetings = cursor.fetchall()
            
            status_list = []
            for meeting in meetings:
                status_list.append({
                    "id": meeting[0],
                    "title": meeting[1],
                    "guest": meeting[2],
                    "datetime": meeting[3],
                    "status": meeting[4],
                    "response_count": meeting[5]
                })
            
            return jsonify({
                "success": True,
                "meetings": status_list
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar status de confirmação: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

# =============================
# === THREADS DE BACKGROUND ===
# =============================
def verificar_reunioes_futuras():
    """Thread para verificar reuniões futuras"""
    while True:
        try:
            agora = datetime.now()
            intervalo = agora + timedelta(minutes=10)
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM reunioes 
                    WHERE datetime(data_hora) BETWEEN datetime(?) AND datetime(?)
                ''', (agora.isoformat(), intervalo.isoformat()))
                
                reunioes = cursor.fetchall()
                
                for r in reunioes:
                    local_info = f" no local '{r[8]}'" if len(r) > 8 and r[8] else ""
                    status_info = f" (Status: {r[9]})" if len(r) > 9 else ""
                    logger.info(f"[Notificação] Reunião '{r[1]}' com {r[2]} às {r[3]}{local_info}{status_info}")
                    
        except Exception as e:
            logger.error(f"Erro no agente de notificação: {e}")
        
        time.sleep(60)  # Verifica a cada minuto

def cleanup_old_logs():
    """Limpa logs antigos periodicamente"""
    while True:
        try:
            # Aguarda 24 horas
            time.sleep(24 * 60 * 60)
            
            # Remove logs com mais de 30 dias
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                
                # Limpa logs de WhatsApp
                cursor.execute('''
                    DELETE FROM whatsapp_logs 
                    WHERE sent_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_logs = cursor.rowcount
                
                # Limpa respostas antigas
                cursor.execute('''
                    DELETE FROM client_responses 
                    WHERE received_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_responses = cursor.rowcount
                conn.commit()
                
                if deleted_logs > 0 or deleted_responses > 0:
                    logger.info(f"Limpeza realizada: {deleted_logs} logs e {deleted_responses} respostas removidas")
                    
        except Exception as e:
            logger.error(f"Erro na limpeza de logs: {e}")

# ===============================
# === ROTA NOVO CLIENTE =========
# ===============================

@app.route('/api/clientes/adicionar', methods=['POST'])
@login_requerido
def adicionar_cliente():
    """
    Adiciona novo cliente à planilha e ao cache
    
    Body JSON esperado:
    {
        "nome": "João Silva",
        "empresa": "Tech Solutions LTDA",
        "whatsapp": "5511999999999"
    }
    """
    try:
        import pandas as pd
        import os
        import re
        from datetime import datetime
        
        logger.info("🔵 Iniciando adição de novo cliente...")
        
        # ═══════════════════════════════════════════════════════════════
        # 1. COLETA DADOS
        # ═══════════════════════════════════════════════════════════════
        
        data = request.get_json() or {}
        
        nome = data.get('nome', '').strip()
        empresa = data.get('empresa', '').strip()
        whatsapp_raw = data.get('whatsapp', '').strip()
        
        logger.debug(f"Dados recebidos: nome='{nome}', empresa='{empresa}', whatsapp='{whatsapp_raw}'")
        
        # ═══════════════════════════════════════════════════════════════
        # 2. VALIDAÇÕES
        # ═══════════════════════════════════════════════════════════════
        
        # Validar nome
        if not nome or len(nome) < 3:
            logger.warning("❌ Nome inválido ou muito curto")
            return jsonify({
                'success': False,
                'message': '❌ Nome inválido (mínimo 3 caracteres)',
                'field': 'nome'
            }), 400
        
        # Validar empresa
        if not empresa or len(empresa) < 3:
            logger.warning("❌ Empresa inválida ou muito curta")
            return jsonify({
                'success': False,
                'message': '❌ Empresa inválida (mínimo 3 caracteres)',
                'field': 'empresa'
            }), 400
        
        # Validar WhatsApp
        whatsapp_limpo = re.sub(r'\D', '', whatsapp_raw)
        
        if not whatsapp_limpo or len(whatsapp_limpo) < 10 or len(whatsapp_limpo) > 13:
            logger.warning(f"❌ WhatsApp inválido: {whatsapp_raw}")
            return jsonify({
                'success': False,
                'message': '❌ WhatsApp inválido (deve ter 10-13 dígitos)',
                'field': 'whatsapp'
            }), 400
        
        # Normaliza WhatsApp
        try:
            whatsapp_normalizado = cliente_autocomplete.normalize_whatsapp(whatsapp_raw)
        except:
            whatsapp_normalizado = whatsapp_limpo
        
        logger.info(f"✅ Validações passadas: {nome} | {empresa} | {whatsapp_normalizado}")
        
        # ═══════════════════════════════════════════════════════════════
        # 3. CARREGAR PLANILHA
        # ═══════════════════════════════════════════════════════════════
        
        arquivo_clientes = 'clientes.xlsx'
        
        # Verifica se arquivo existe
        if os.path.exists(arquivo_clientes):
            logger.info(f"📂 Carregando planilha existente: {arquivo_clientes}")
            try:
                df = pd.read_excel(arquivo_clientes, engine='openpyxl')
            except Exception as e:
                logger.debug(f"Falha com openpyxl: {e}, tentando xlrd...")
                try:
                    df = pd.read_excel(arquivo_clientes, engine='xlrd')
                except:
                    logger.warning("Criando nova planilha...")
                    df = pd.DataFrame(columns=['NOME', 'EMPRESA', 'WHATSAPP'])
        else:
            logger.info(f"📝 Criando nova planilha: {arquivo_clientes}")
            df = pd.DataFrame(columns=['NOME', 'EMPRESA', 'WHATSAPP'])
        
        # Normaliza nomes das colunas
        df.columns = df.columns.str.strip().str.upper()
        
        # Garante que as colunas necessárias existem
        colunas_necessarias = ['NOME', 'EMPRESA', 'WHATSAPP']
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = ''
        
        logger.debug(f"Colunas da planilha: {list(df.columns)}")
        
        # ═══════════════════════════════════════════════════════════════
        # 4. VERIFICAR DUPLICATAS
        # ═══════════════════════════════════════════════════════════════
        
        # Normaliza nomes para comparação
        df['NOME_NORM'] = df['NOME'].str.upper().str.strip() if 'NOME' in df.columns else ''
        nome_normalizado = nome.upper().strip()
        
        # Verifica se nome já existe
        if nome_normalizado in df['NOME_NORM'].values:
            logger.warning(f"⚠️ Cliente '{nome}' já existe na planilha")
            
            cliente_existente = df[df['NOME_NORM'] == nome_normalizado].iloc[0]
            df = df.drop('NOME_NORM', axis=1)
            
            return jsonify({
                'success': False,
                'message': f"⚠️ Cliente '{nome}' já existe na planilha",
                'cliente_existente': {
                    'nome': str(cliente_existente.get('NOME', '')),
                    'empresa': str(cliente_existente.get('EMPRESA', '')),
                    'whatsapp': str(cliente_existente.get('WHATSAPP', ''))
                }
            }), 409
        
        # Remove coluna temporária
        df = df.drop('NOME_NORM', axis=1)
        
        # ═══════════════════════════════════════════════════════════════
        # 5. ADICIONAR NOVO CLIENTE
        # ═══════════════════════════════════════════════════════════════
        
        novo_cliente = {
            'NOME': nome,
            'EMPRESA': empresa,
            'WHATSAPP': whatsapp_normalizado
        }
        
        # Adiciona nova linha
        df = pd.concat([df, pd.DataFrame([novo_cliente])], ignore_index=True)
        
        logger.info(f"✅ Novo cliente adicionado: {nome}")
        logger.debug(f"Planilha agora tem {len(df)} clientes")
        
        # ═══════════════════════════════════════════════════════════════
        # 6. SALVAR PLANILHA
        # ═══════════════════════════════════════════════════════════════
        
        try:
            with pd.ExcelWriter(arquivo_clientes, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Clientes', index=False)
            
            logger.info(f"💾 Planilha salva com sucesso: {arquivo_clientes}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar planilha: {e}")
            return jsonify({
                'success': False,
                'message': f"Erro ao salvar planilha: {str(e)}"
            }), 500
        
        # ═══════════════════════════════════════════════════════════════
        # 7. LIMPAR CACHE
        # ═══════════════════════════════════════════════════════════════
        
        try:
            cliente_autocomplete.clear_cache()
            logger.info("🔄 Cache de clientes limpo")
        except Exception as e:
            logger.debug(f"Aviso ao limpar cache: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 8. RETORNAR SUCESSO
        # ═══════════════════════════════════════════════════════════════
        
        resposta = {
            'success': True,
            'message': '✅ Cliente adicionado com sucesso!',
            'cliente': {
                'nome': nome,
                'empresa': empresa,
                'whatsapp': whatsapp_normalizado,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"✅ Resposta de sucesso enviada para '{nome}'")
        
        return jsonify(resposta), 201
        
    except ValueError as e:
        logger.error(f"❌ Erro de validação: {e}")
        return jsonify({
            'success': False,
            'message': f"Erro de validação: {str(e)}"
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Erro não tratado: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Erro ao adicionar cliente: {str(e)}"
        }), 500


# ===============================
# === ROTAS AUTOCOMPLETE ========
# ===============================

@app.route('/api/clientes/search', methods=['GET'])
@login_requerido
def api_search_clientes():
    """API para buscar clientes via autocomplete"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        # Validação básica
        if not query:
            return jsonify({
                'success': True,
                'clientes': [],
                'message': 'Digite o nome do cliente',
                'query': query
            })
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'clientes': [],
                'message': 'Digite pelo menos 2 caracteres',
                'query': query
            })
        
        # Busca clientes
        clientes = cliente_autocomplete.search_clientes(query, limit)
        
        # Log da busca
        logger.info(f"🔍 Busca autocomplete: '{query}' → {len(clientes)} resultados")
        
        return jsonify({
            'success': True,
            'clientes': clientes,
            'query': query,
            'total': len(clientes),
            'message': f'{len(clientes)} clientes encontrados' if clientes else 'Nenhum cliente encontrado'
        })
        
    except Exception as e:
        logger.error(f"Erro na busca de clientes: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}',
            'clientes': [],
            'query': request.args.get('q', '')
        }), 500

@app.route('/api/clientes/reload', methods=['POST'])
@login_requerido
def api_reload_clientes():
    """Recarrega cache de clientes da planilha"""
    try:
        # Limpa cache atual
        cliente_autocomplete.clear_cache()
        
        # Recarrega dados
        clientes = cliente_autocomplete.load_clientes_from_excel()
        
        logger.info(f"📊 Cache de clientes recarregado: {len(clientes)} registros")
        
        return jsonify({
            'success': True,
            'message': f'Cache recarregado com sucesso! {len(clientes)} clientes disponíveis',
            'total': len(clientes),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao recarregar clientes: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao recarregar: {str(e)}'
        }), 500

@app.route('/api/clientes/stats', methods=['GET'])
@login_requerido
def api_clientes_stats():
    """Estatísticas dos clientes carregados"""
    try:
        stats = cliente_autocomplete.get_clientes_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/clientes/validate', methods=['GET'])
@login_requerido
def api_validate_clientes():
    """Valida arquivo de clientes"""
    try:
        validation = cliente_autocomplete.validate_clientes_file()
        
        return jsonify({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/system/autocomplete-status', methods=['GET'])
@login_requerido
def api_autocomplete_status():
    """Status geral do sistema de autocomplete"""
    try:
        # Validação do arquivo
        validation = cliente_autocomplete.validate_clientes_file()
        
        # Estatísticas se arquivo OK
        stats = {}
        if validation['file_exists'] and validation['has_data']:
            stats = cliente_autocomplete.get_clientes_stats()
        
        # Info do cache
        cache_info = {
            'cached': cliente_autocomplete._clientes_cache is not None,
            'cache_timestamp': cliente_autocomplete._cache_timestamp.isoformat() if cliente_autocomplete._cache_timestamp else None,
            'cache_size': len(cliente_autocomplete._clientes_cache) if cliente_autocomplete._clientes_cache else 0
        }
        
        # Status geral
        status = {
            'system_ready': validation['file_exists'] and validation['has_data'],
            'file_validation': validation,
            'cache_info': cache_info,
            'stats': stats,
            'dependencies': {
                'pandas_available': True,
                'fuzzy_available': cliente_autocomplete.FUZZY_AVAILABLE
            }
        }
        
        return jsonify({
            'success': True,
            'status': status,
            'message': 'Sistema de autocomplete funcionando' if status['system_ready'] else 'Sistema com problemas'
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500
# =============================
# === DISPARADOR DE ANIVERSÁRIOS ===
# =============================
# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
FIXED_SPREADSHEET = 'ANIVERSARIOS_CLIENTES.xls'  # Planilha fixa

# Certifica que a pasta de upload existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_excel_date(excel_date):
    """Converte data serial do Excel para datetime"""
    try:
        # Se já é uma string de data
        if isinstance(excel_date, str):
            # Tenta vários formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(excel_date, fmt).date()
                except ValueError:
                    continue
            return None
        
        # Se é um número (data serial do Excel)
        elif isinstance(excel_date, (int, float)):
            # Excel usa 1900-01-01 como base (com bug do ano 1900)
            if excel_date > 59:  # Após 29/02/1900 (que não existe)
                base_date = datetime(1899, 12, 30)  # Compensa o bug
            else:
                base_date = datetime(1899, 12, 31)
            
            return (base_date + timedelta(days=excel_date)).date()
        
        # Se já é datetime
        elif hasattr(excel_date, 'date'):
            return excel_date.date()
        
        return None
        
    except Exception as e:
        print(f"Erro ao converter data {excel_date}: {e}")
        return None

def clean_whatsapp(whatsapp):
    """CORRIGIDO: Normalização consistente para aniversários"""
    if pd.isna(whatsapp):
        return None
    
    clean = re.sub(r'\D', '', str(whatsapp))
    
    # Aplicar mesma lógica da classe principal
    if len(clean) == 11 and clean[2] == '9':
        clean = '55' + clean
    elif len(clean) == 10:
        ddd = clean[:2]
        numero = clean[2:]
        clean = f"55{ddd}9{numero}"
    elif len(clean) == 12 and clean.startswith('55'):
        # Adicionar o 9
        clean = clean[:4] + '9' + clean[4:]
    
    return clean if len(clean) >= 12 else None

def sync_from_fixed_spreadsheet():
    """Sincroniza planilha CORRIGIDA - previne duplicatas definitivamente"""
    try:
        FIXED_SPREADSHEET = 'ANIVERSARIOS_CLIENTES.xls'
        
        if not os.path.exists(FIXED_SPREADSHEET):
            return False, f"Planilha {FIXED_SPREADSHEET} não encontrada"
        
        logger.info(f"📊 Lendo planilha: {FIXED_SPREADSHEET}")
        
        # CORREÇÃO: Lê com engine apropriada
        try:
            df = pd.read_excel(FIXED_SPREADSHEET, engine='xlrd')
            logger.info(f"✅ Planilha lida com xlrd")
        except Exception as e1:
            logger.warning(f"⚠️ xlrd falhou: {e1}")
            try:
                df = pd.read_excel(FIXED_SPREADSHEET, engine='openpyxl')
                logger.info(f"✅ Planilha lida com openpyxl")
            except Exception as e2:
                return False, f"❌ Erro ao ler planilha - xlrd: {e1} | openpyxl: {e2}"
        
        if df.empty:
            return False, "Planilha está vazia"
        
        # Normaliza colunas
        df.columns = df.columns.str.strip().str.upper()
        logger.info(f"📋 Colunas: {list(df.columns)}")
        logger.info(f"📊 Total de linhas: {len(df)}")
        
        # CORREÇÃO: Mapeamento robusto de colunas
        required_mapping = {
            'NOME': ['NOME', 'NAME', 'CLIENTE', 'PERSON'],
            'NASCIMENTO': ['NASCIMENTO', 'BIRTHDAY', 'DATA_NASCIMENTO', 'ANIVERSARIO', 'BIRTH'],
            'WHATSAPP': ['WHATSAPP', 'TELEFONE', 'PHONE', 'CELULAR', 'MOBILE']
        }
        
        column_map = {}
        for required, alternatives in required_mapping.items():
            found_column = None
            for alt in alternatives:
                if alt in df.columns:
                    found_column = alt
                    break
            
            if found_column:
                column_map[required] = found_column
                logger.info(f"✅ {required} → {found_column}")
            else:
                return False, f'❌ Coluna obrigatória não encontrada: {required}. Disponíveis: {list(df.columns)}'
        
        # CORREÇÃO: Usa transação completa
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        try:
            # Inicia transação
            cursor.execute('BEGIN TRANSACTION')
            
            imported_count = 0
            updated_count = 0
            duplicate_count = 0
            error_count = 0
            errors = []
            
            # CORREÇÃO: Não marca como inativo - processa linha por linha
            processed_combinations = set()
            
            for index, row in df.iterrows():
                try:
                    # Extrai dados
                    nome_raw = str(row[column_map['NOME']]).strip()
                    empresa = str(row.get('EMPRESA', '')).strip() if 'EMPRESA' in df.columns else ''
                    nascimento_raw = row[column_map['NASCIMENTO']]
                    whatsapp_raw = str(row[column_map['WHATSAPP']]).strip()
                    
                    # Validação nome
                    if not nome_raw or nome_raw.lower() in ['nan', 'none', '']:
                        errors.append(f'Linha {index + 2}: Nome inválido - "{nome_raw}"')
                        error_count += 1
                        continue
                    
                    nome = nome_raw.upper().strip()
                    
                    # CORREÇÃO: Normalização consistente WhatsApp
                    whatsapp_clean = re.sub(r'\D', '', whatsapp_raw)
                    
                    # Aplica regras de normalização brasileira
                    if len(whatsapp_clean) == 10:
                        # Formato antigo: adiciona 55 + 9
                        ddd = whatsapp_clean[:2]
                        numero = whatsapp_clean[2:]
                        whatsapp_normalized = f"55{ddd}9{numero}"
                    elif len(whatsapp_clean) == 11:
                        # Formato atual: adiciona 55
                        whatsapp_normalized = f"55{whatsapp_clean}"
                    elif len(whatsapp_clean) == 12 and whatsapp_clean.startswith('55'):
                        # Formato antigo internacional: adiciona 9
                        whatsapp_normalized = f"{whatsapp_clean[:4]}9{whatsapp_clean[4:]}"
                    elif len(whatsapp_clean) == 13 and whatsapp_clean.startswith('55'):
                        # Já normalizado
                        whatsapp_normalized = whatsapp_clean
                    else:
                        errors.append(f'Linha {index + 2}: WhatsApp inválido - "{whatsapp_raw}" -> "{whatsapp_clean}"')
                        error_count += 1
                        continue
                    
                    # CORREÇÃO: Conversão robusta de data
                    nascimento = None
                    if pd.isna(nascimento_raw):
                        errors.append(f'Linha {index + 2}: Data de nascimento vazia')
                        error_count += 1
                        continue
                    
                    if isinstance(nascimento_raw, str):
                        # Tenta diferentes formatos de string
                        for date_format in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                            try:
                                nascimento = datetime.strptime(nascimento_raw, date_format).date()
                                break
                            except ValueError:
                                continue
                    elif isinstance(nascimento_raw, (int, float)):
                        # Data serial do Excel
                        try:
                            if nascimento_raw > 59:
                                base_date = datetime(1899, 12, 30)
                            else:
                                base_date = datetime(1899, 12, 31)
                            nascimento = (base_date + timedelta(days=int(nascimento_raw))).date()
                        except Exception as e:
                            errors.append(f'Linha {index + 2}: Erro ao converter data serial {nascimento_raw}: {e}')
                            error_count += 1
                            continue
                    elif hasattr(nascimento_raw, 'date'):
                        nascimento = nascimento_raw.date()
                    
                    if not nascimento:
                        errors.append(f'Linha {index + 2}: Não foi possível converter data "{nascimento_raw}"')
                        error_count += 1
                        continue
                    
                    # CHAVE CRÍTICA: nome + nascimento (não WhatsApp)
                    unique_key = f"{nome}|{nascimento}"
                    
                    # Verifica duplicata na própria planilha
                    if unique_key in processed_combinations:
                        errors.append(f'Linha {index + 2}: Duplicata na planilha - {nome} ({nascimento})')
                        duplicate_count += 1
                        continue
                    
                    processed_combinations.add(unique_key)
                    
                    # CORREÇÃO: Busca por nome + nascimento
                    cursor.execute('''
                        SELECT id, whatsapp, empresa FROM aniversariantes 
                        WHERE UPPER(TRIM(nome)) = ? AND nascimento = ?
                    ''', (nome, nascimento))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        existing_id, existing_whatsapp, existing_empresa = existing
                        
                        # Atualiza dados se mudaram
                        cursor.execute('''
                            UPDATE aniversariantes 
                            SET whatsapp = ?, empresa = ?, ativo = 1 
                            WHERE id = ?
                        ''', (whatsapp_normalized, empresa, existing_id))
                        
                        updated_count += 1
                        
                        # Log de mudanças
                        changes = []
                        if existing_whatsapp != whatsapp_normalized:
                            changes.append(f"WhatsApp: {existing_whatsapp} → {whatsapp_normalized}")
                        if existing_empresa != empresa:
                            changes.append(f"Empresa: '{existing_empresa}' → '{empresa}'")
                        
                        if changes:
                            logger.info(f"🔄 Atualizado {nome}: {', '.join(changes)}")
                    
                    else:
                        # INSERE NOVO
                        cursor.execute('''
                            INSERT INTO aniversariantes (nome, empresa, nascimento, whatsapp, ativo)
                            VALUES (?, ?, ?, ?, 1)
                        ''', (nome_raw, empresa, nascimento, whatsapp_normalized))
                        
                        imported_count += 1
                        logger.info(f"➕ Novo: {nome_raw} ({nascimento}) - {whatsapp_normalized}")
                
                except Exception as e:
                    error_msg = f'Linha {index + 2}: Erro interno - {str(e)}'
                    errors.append(error_msg)
                    error_count += 1
                    logger.error(error_msg)
            
            # Commit da transação
            cursor.execute('COMMIT')
            
            logger.info(f"✅ Sincronização concluída:")
            logger.info(f"   ➕ {imported_count} novos registros")
            logger.info(f"   🔄 {updated_count} atualizados")
            logger.info(f"   🔁 {duplicate_count} duplicatas ignoradas")
            logger.info(f"   ❌ {error_count} erros")
            
            return True, {
                'imported_count': imported_count,
                'updated_count': updated_count,
                'duplicate_count': duplicate_count,
                'error_count': error_count,
                'errors': errors[:10],  # Primeiros 10 erros
                'total_errors': error_count
            }
            
        except Exception as e:
            # ROLLBACK em caso de erro
            cursor.execute('ROLLBACK')
            raise e
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro crítico na sincronização: {e}")
        return False, f"Erro crítico: {str(e)}"
        
def clean_existing_duplicates():
    """Remove duplicatas existentes baseado em nome + nascimento"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        logger.info("🔍 Buscando duplicatas...")
        
        # CORREÇÃO: Busca duplicatas por nome + nascimento
        cursor.execute('''
            SELECT UPPER(TRIM(nome)), nascimento, COUNT(*) as total,
                   GROUP_CONCAT(id) as ids
            FROM aniversariantes 
            GROUP BY UPPER(TRIM(nome)), nascimento
            HAVING COUNT(*) > 1
            ORDER BY total DESC
        ''')
        
        duplicates = cursor.fetchall()
        removed_count = 0
        
        logger.info(f"📊 Encontrados {len(duplicates)} grupos de duplicatas")
        
        for nome_upper, nascimento, total, ids_str in duplicates:
            ids = [int(x) for x in ids_str.split(',')]
            logger.info(f"🔄 Processando: {nome_upper} ({nascimento}) - {total} registros")
            
            # Busca detalhes de todos os registros
            cursor.execute(f'''
                SELECT id, nome, empresa, whatsapp, data_cadastro
                FROM aniversariantes 
                WHERE id IN ({','.join(['?' for _ in ids])})
                ORDER BY data_cadastro DESC, id DESC
            ''', ids)
            
            records = cursor.fetchall()
            
            # Mantém o primeiro (mais recente) e remove os outros
            keep_record = records[0]
            remove_records = records[1:]
            
            logger.info(f"✅ Mantendo: ID {keep_record[0]} - {keep_record[1]}")
            
            for record in remove_records:
                record_id = record[0]
                
                # Remove logs relacionados primeiro
                cursor.execute('DELETE FROM logs_aniversarios WHERE aniversariante_id = ?', (record_id,))
                
                # Remove o aniversariante
                cursor.execute('DELETE FROM aniversariantes WHERE id = ?', (record_id,))
                
                logger.info(f"🗑️ Removido: ID {record_id} - {record[1]}")
                removed_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧹 Limpeza concluída: {removed_count} duplicatas removidas")
        
        return True, {
            'success': True,
            'removed_count': removed_count,
            'duplicate_groups': len(duplicates),
            'message': f'{removed_count} registros duplicados removidos de {len(duplicates)} grupos'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar duplicatas: {e}")
        return False, {'success': False, 'message': str(e)}

# Rota adicional para limpeza
@app.route('/api/aniversarios/clean-duplicates', methods=['POST'])
def clean_duplicates_api():
    """API para limpar duplicatas"""
    try:
        success, result = clean_existing_duplicates()
        
        if success:
            return jsonify({
                'success': True,
                'removed_count': result['removed_count'],
                'duplicate_groups': result['duplicate_groups'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            })
            
    except Exception as e:
        logger.error(f"Erro na API de limpeza: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        })


def get_spreadsheet_info():
    """Obtém informações sobre a planilha fixa"""
    try:
        if not os.path.exists(FIXED_SPREADSHEET):
            return {
                'exists': False,
                'last_modified': None,
                'total_records': 0
            }
        
        # Informações do arquivo
        stat = os.stat(FIXED_SPREADSHEET)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Conta registros na planilha
        df = pd.read_excel(FIXED_SPREADSHEET)
        total_records = len(df)
        
        return {
            'exists': True,
            'last_modified': last_modified.strftime('%d/%m/%Y %H:%M:%S'),
            'total_records': total_records,
            'file_size': f"{stat.st_size / 1024:.1f} KB"
        }
        
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }

def init_birthday_db():
    """Inicializa banco CORRIGIDO com tratamento de erros"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        # CORREÇÃO: Verifica se tabelas existem antes de criar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aniversariantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                empresa TEXT DEFAULT '',
                nascimento DATE NOT NULL,
                whatsapp TEXT NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_aniversarios (
                id INTEGER PRIMARY KEY,
                horario_envio TEXT DEFAULT '09:00',
                dias_antecedencia INTEGER DEFAULT 0,
                ativo BOOLEAN DEFAULT 1,
                template_mensagem TEXT DEFAULT 'Parabéns {nome}! 🎉'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_aniversarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aniversariante_id INTEGER,
                nome_aniversariante TEXT,
                empresa_aniversariante TEXT,
                whatsapp TEXT,
                data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                erro TEXT,
                FOREIGN KEY (aniversariante_id) REFERENCES aniversariantes (id)
            )
        """)
        
        # Insere config padrão se não existir
        cursor.execute('SELECT COUNT(*) FROM config_aniversarios')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO config_aniversarios (id, template_mensagem) 
                VALUES (1, 'Olá {nome}! 🎉\n\nParabéns pelo seu aniversário! 🎂\nA equipe deseja muito sucesso!\n\nUm abraço! 🤗')
            ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Banco de aniversários inicializado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de aniversários: {e}")
        return False


def get_birthday_config():
    """Obtém a configuração atual do sistema"""
    conn = sqlite3.connect('sistema.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM config_aniversarios WHERE id = 1')
    config = cursor.fetchone()
    conn.close()
    
    if config:
        return {
            'horario_envio': config[1],
            'dias_antecedencia': config[2],
            'ativo': bool(config[3]),
            'template_mensagem': config[4]
        }
    return {}

# =====================================================
# ADICIONE ESTE CÓDIGO NO SEU app.py
# Logo após a rota /api/reunioes
# =====================================================

@app.route('/api/aniversarios')
def api_aniversarios():
    """
    API para retornar aniversários em formato JSON para o calendário
    Retorna apenas: nome, empresa, data_aniversario
    """
    try:
        conn = sqlite3.connect('sistema.db')  # Banco de aniversários
        cursor = conn.cursor()
        
        # Busca todos os aniversariantes ativos
        cursor.execute('''
            SELECT 
                id,
                nome,
                empresa,
                nascimento,
                whatsapp
            FROM aniversariantes
            WHERE ativo = 1
            ORDER BY nascimento ASC
        ''')
        
        aniversariantes = cursor.fetchall()
        conn.close()
        
        # Converte para lista de dicionários no formato esperado pelo calendário
        aniversarios_list = []
        for aniv in aniversariantes:
            # Extrai mês e dia do nascimento (ignora o ano)
            nascimento_completo = aniv[3]  # YYYY-MM-DD
            
            # Parse da data
            if isinstance(nascimento_completo, str):
                # Formato: YYYY-MM-DD
                partes = nascimento_completo.split('-')
                if len(partes) == 3:
                    mes = partes[1].zfill(2)
                    dia = partes[2].zfill(2)
                    data_aniversario = f"{mes}-{dia}"  # MM-DD
                else:
                    continue
            else:
                # Se vier como date object
                from datetime import datetime
                if hasattr(nascimento_completo, 'month'):
                    mes = str(nascimento_completo.month).zfill(2)
                    dia = str(nascimento_completo.day).zfill(2)
                    data_aniversario = f"{mes}-{dia}"
                else:
                    continue
            
            aniversarios_list.append({
                'id': aniv[0],
                'nome': aniv[1],
                'empresa': aniv[2] or '',
                'data_aniversario': data_aniversario,  # Formato: MM-DD
                'telefone': aniv[4] or '',  # Opcional para futuras funcionalidades
                'nascimento_completo': nascimento_completo  # Para cálculo de idade se necessário
            })
        
        logger.info(f"📅 API Aniversários: {len(aniversarios_list)} registros retornados")
        
        return jsonify(aniversarios_list)
        
    except Exception as e:
        logger.error(f"Erro ao buscar aniversários para API: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify([]), 500


@app.route('/api/aniversarios/sync-check', methods=['GET'])
def sync_check():
    """
    Verifica status da sincronização de aniversários
    Útil para debug
    """
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        # Total no banco
        cursor.execute('SELECT COUNT(*) FROM aniversariantes WHERE ativo = 1')
        total_banco = cursor.fetchone()[0]
        
        # Aniversários deste mês
        mes_atual = datetime.now().strftime('%m')
        cursor.execute('''
            SELECT COUNT(*) FROM aniversariantes 
            WHERE ativo = 1 AND strftime('%m', nascimento) = ?
        ''', (mes_atual,))
        mes_atual_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Verifica se planilha existe
        import os
        planilha_existe = os.path.exists('ANIVERSARIOS_CLIENTES.xls')
        
        return jsonify({
            'success': True,
            'banco': {
                'total_ativos': total_banco,
                'mes_atual': mes_atual_count
            },
            'planilha': {
                'existe': planilha_existe,
                'caminho': 'ANIVERSARIOS_CLIENTES.xls'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no sync-check: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
# =====================================================
                                                  #^
# API aniversários - MÉTODOS DE ENVIO DE MENSAGENS |

# =====================================================
# ===============================
# CORREÇÃO 3: MÉTODO COM RETRY AUTOMÁTICO (RECOMENDADO)
# ===============================
# Adicione este método na classe EvolutionAPIManager para melhor compatibilidade

def send_message_with_retry(self, phone: str, message: str, max_retries: int = 3) -> Tuple[bool, str]:
    """Envia mensagem com retry automático e múltiplos formatos"""
    
    # Formatos possíveis da Evolution API
    formats = [
        # Formato v2.x mais recente
        {
            "name": "v2_textMessage",
            "data": lambda phone, msg: {
                "number": phone,
                "textMessage": {"text": msg}
            }
        },
        # Formato v1.x tradicional (fallback)
        {
            "name": "v1_text",
            "data": lambda phone, msg: {
                "number": phone,
                "text": msg
            }
        },
        # Formato alternativo com options
        {
            "name": "v2_with_options",
            "data": lambda phone, msg: {
                "number": phone,
                "textMessage": {
                    "text": msg
                },
                "options": {
                    "delay": 1200,
                    "presence": "composing"
                }
            }
        }
    ]
    
    normalized_phone = self.normalize_phone_number(phone)
    logger.info(f"Tentando enviar mensagem para: {normalized_phone}")
    
    last_error = ""
    
    for fmt in formats:
        logger.info(f"Tentando formato: {fmt['name']}")
        
    for attempt in range(max_retries):
            try:
                data = fmt['data'](normalized_phone, message)
                
                success, result = self._make_request('POST', f'/message/sendText/{self.instance_name}', data)
                
                if success:
                    logger.info(f"✅ Mensagem enviada com sucesso usando formato {fmt['name']} (tentativa {attempt + 1})")
                    return True, f"Mensagem enviada com sucesso (formato: {fmt['name']})"
                
                error_msg = result.get('error', 'Erro desconhecido')
                last_error = f"Formato {fmt['name']}: {error_msg}"
                
                # Se é erro de formato, pula para próximo formato
                if any(keyword in str(error_msg).lower() for keyword in ['textmessage', 'text', 'property', 'requires']):
                    logger.warning(f"Erro de formato detectado no {fmt['name']}, tentando próximo formato...")
                    break
                
                # Se é outro tipo de erro, tenta novamente com mesmo formato
                if attempt < max_retries - 1:
                    logger.warning(f"Tentativa {attempt + 1} falhou com {fmt['name']}, tentando novamente...")
                    time.sleep(1)
                
            except Exception as e:
                last_error = f"Erro interno no formato {fmt['name']}: {str(e)}"
                logger.error(last_error)
                if attempt < max_retries - 1:
                    time.sleep(1)
    
    logger.error(f"❌ Falha ao enviar mensagem após tentar todos os formatos")
    return False, f"Falha após {max_retries} tentativas com todos os formatos. Último erro: {last_error}"

def calculate_age(birth_date):
    """Calcula a idade baseada na data de nascimento"""
    today = datetime.now()
    if isinstance(birth_date, str):
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
    else:
        birth = datetime.combine(birth_date, datetime.min.time())
    
    age = today.year - birth.year
    if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
        age -= 1
    return age

# ===================== ROTAS DO SISTEMA DE ANIVERSÁRIOS =====================

@app.route('/disparador')
def disparador():
    """Página principal do sistema de aniversários"""
    # Garante que o banco está inicializado quando acessar a página
    init_birthday_db()
    return render_template('disparo.html', titulo="Sistema de Aniversários")

@app.route('/api/aniversarios/init-db', methods=['POST'])
def init_db_route():
    """Rota para inicializar/reinicializar o banco de dados"""
    try:
        init_birthday_db()
        return jsonify({'success': True, 'message': 'Banco de dados inicializado com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/dashboard')
def dashboard_aniversarios():
    """Dashboard com estatísticas"""
    try:
        # Garante que o banco está inicializado
        init_birthday_db()
        
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        # Total de aniversariantes
        cursor.execute('SELECT COUNT(*) FROM aniversariantes WHERE ativo = 1')
        total_aniversariantes = cursor.fetchone()[0]
        
        # Aniversários hoje
        today = datetime.now().strftime('%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM aniversariantes 
            WHERE ativo = 1 AND strftime('%m-%d', nascimento) = ?
        ''', (today,))
        aniversarios_hoje = cursor.fetchone()[0]
        
        # Próximos 7 dias
        dates_7_days = []
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime('%m-%d')
            dates_7_days.append(date)
        
        placeholders = ','.join(['?' for _ in dates_7_days])
        cursor.execute(f'''
            SELECT COUNT(*) FROM aniversariantes 
            WHERE ativo = 1 AND strftime('%m-%d', nascimento) IN ({placeholders})
        ''', dates_7_days)
        proximos_7_dias = cursor.fetchone()[0]
        
        # Enviados hoje
        cursor.execute('''
            SELECT COUNT(*) FROM logs_aniversarios 
            WHERE DATE(data_envio) = DATE('now') AND status = 'success'
        ''')
        enviados_hoje = cursor.fetchone()[0]
        
        # Lista de aniversariantes de hoje
        cursor.execute('''
            SELECT a.*, l.status as enviado 
            FROM aniversariantes a
            LEFT JOIN logs_aniversarios l ON a.id = l.aniversariante_id 
                AND DATE(l.data_envio) = DATE('now')
            WHERE a.ativo = 1 AND strftime('%m-%d', a.nascimento) = ?
        ''', (today,))
        
        aniversariantes_hoje = []
        for row in cursor.fetchall():
            aniversariantes_hoje.append({
                'id': row[0],
                'nome': row[1],
                'empresa': row[2],
                'nascimento': row[3],
                'whatsapp': row[4],
                'enviado': row[7] == 'success' if row[7] else False
            })
        
        conn.close()
        
        # Informações da planilha fixa
        spreadsheet_info = get_spreadsheet_info()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_aniversariantes': total_aniversariantes,
                'aniversarios_hoje': aniversarios_hoje,
                'proximos_7_dias': proximos_7_dias,
                'enviados_hoje': enviados_hoje
            },
            'aniversarios_hoje': aniversariantes_hoje,
            'spreadsheet_info': spreadsheet_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/sync-spreadsheet', methods=['POST'])
def sync_spreadsheet():
    """Sincroniza dados da planilha fixa"""
    try:
        # Garante que o banco está inicializado
        init_birthday_db()
        
        success, result = sync_from_fixed_spreadsheet()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sincronização concluída!',
                'imported_count': result['imported_count'],
                'updated_count': result['updated_count'],
                'error_count': result['error_count'],
                'errors': result['errors'],
                'total_errors': result['total_errors']
            })
        else:
            return jsonify({'success': False, 'message': result})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/upload-spreadsheet', methods=['POST'])
def upload_spreadsheet():
    """Faz upload da nova planilha fixa"""
    try:
        # Garante que o banco está inicializado
        init_birthday_db()
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
        
        if file and allowed_file(file.filename):
            # Salva como planilha fixa
            file.save(FIXED_SPREADSHEET)
            
            # Sincroniza automaticamente
            success, result = sync_from_fixed_spreadsheet()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Planilha atualizada e sincronizada com sucesso!',
                    'imported_count': result['imported_count'],
                    'updated_count': result['updated_count'],
                    'error_count': result['error_count'],
                    'errors': result['errors'][:5],  # Mostra apenas os primeiros 5 erros
                    'total_errors': result['total_errors']
                })
            else:
                return jsonify({'success': False, 'message': f'Planilha salva, mas erro na sincronização: {result}'})
                
        else:
            return jsonify({'success': False, 'message': 'Formato de arquivo não suportado'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/import', methods=['POST'])
def import_aniversarios():
    """Importa planilha de aniversariantes (mantido para compatibilidade)"""
    return upload_spreadsheet()

@app.route('/api/aniversarios/list')
def list_aniversarios():
    """Lista todos os aniversariantes"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nome, empresa, nascimento, whatsapp, ativo
            FROM aniversariantes
            ORDER BY nome
        ''')
        
        aniversariantes = []
        for row in cursor.fetchall():
            aniversariantes.append({
                'id': row[0],
                'nome': row[1],
                'empresa': row[2],
                'nascimento': row[3],
                'whatsapp': row[4],
                'ativo': bool(row[5])
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'aniversariantes': aniversariantes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/config', methods=['GET', 'POST'])
def config_aniversarios():
    """Gerencia configurações do sistema"""
    if request.method == 'GET':
        try:
            config = get_birthday_config()
            return jsonify({'success': True, 'config': config})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            conn = sqlite3.connect('sistema.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE config_aniversarios 
                SET horario_envio = ?, dias_antecedencia = ?, ativo = ?, template_mensagem = ?
                WHERE id = 1
            ''', (
                data.get('horario_envio', '09:00'),
                data.get('dias_antecedencia', 0),
                data.get('ativo', True),
                data.get('template_mensagem', '')
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Configurações salvas com sucesso!'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/check-today', methods=['POST'])
def check_today_birthdays():
    """Verifica e envia mensagens para aniversariantes de hoje"""
    try:
        config = get_birthday_config()
        if not config.get('ativo', False):
            return jsonify({'success': False, 'message': 'Sistema desativado nas configurações'})
        
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        # Calcula a data alvo (hoje - dias de antecedência)
        target_date = datetime.now() + timedelta(days=config.get('dias_antecedencia', 0))
        target_date_str = target_date.strftime('%m-%d')
        
        # Busca aniversariantes do dia
        cursor.execute('''
            SELECT a.* FROM aniversariantes a
            WHERE a.ativo = 1 AND strftime('%m-%d', a.nascimento) = ?
            AND NOT EXISTS (
                SELECT 1 FROM logs_aniversarios l 
                WHERE l.aniversariante_id = a.id 
                AND DATE(l.data_envio) = DATE('now')
                AND l.status = 'success'
            )
        ''', (target_date_str,))
        
        aniversariantes = cursor.fetchall()
        sent_count = 0
        
        template = config.get('template_mensagem', 'Parabéns {nome}! 🎉')
        
        for aniversariante in aniversariantes:
            try:
                id_aniv, nome, empresa, nascimento, whatsapp, ativo, _ = aniversariante
                
                # Calcula idade
                idade = calculate_age(nascimento)
                
                # Monta mensagem
                message = template.format(
                    nome=nome,
                    empresa=empresa or 'nossa equipe',
                    idade=idade
                )
                
                # CORREÇÃO AQUI: Usar a função renomeada
                success, response = send_birthday_whatsapp_message(whatsapp, message)
                
                # Registra log
                cursor.execute('''
                    INSERT INTO logs_aniversarios 
                    (aniversariante_id, nome_aniversariante, empresa_aniversariante, whatsapp, data_envio, status, erro)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    id_aniv, nome, empresa, whatsapp, datetime.now(),
                    'success' if success else 'error',
                    None if success else str(response)
                ))
                
                if success:
                    sent_count += 1
                    
            except Exception as e:
                # Registra erro no log
                cursor.execute('''
                    INSERT INTO logs_aniversarios 
                    (aniversariante_id, nome_aniversariante, whatsapp, data_envio, status, erro)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (id_aniv, nome, whatsapp, datetime.now(), 'error', str(e)))
        
        conn.commit()
        conn.close()
        
        if sent_count > 0:
            return jsonify({
                'success': True,
                'sent_count': sent_count,
                'message': f'{sent_count} mensagens enviadas com sucesso!'
            })
        else:
            return jsonify({
                'success': True,
                'sent_count': 0,
                'message': 'Nenhum aniversariante encontrado ou todas as mensagens já foram enviadas hoje.'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/api/aniversarios/test-message/<int:id>', methods=['POST'])
def test_message(id):
    """Envia mensagem de teste para um aniversariante específico"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM aniversariantes WHERE id = ?', (id,))
        aniversariante = cursor.fetchone()
        
        if not aniversariante:
            return jsonify({'success': False, 'message': 'Aniversariante não encontrado'})
        
        _, nome, empresa, nascimento, whatsapp, _, _ = aniversariante
        
        config = get_birthday_config()
        template = config.get('template_mensagem', 'Mensagem de teste para {nome}! 🧪')
        
        idade = calculate_age(nascimento)
        
        message = f" {template}".format(
            nome=nome,
            empresa=empresa or 'nossa equipe',
            idade=idade
        )
        
        # CORREÇÃO AQUI: Usar a função renomeada
        success, response = send_birthday_whatsapp_message(whatsapp, message)
        
        # Registra log do teste
        cursor.execute('''
            INSERT INTO logs_aniversarios 
            (aniversariante_id, nome_aniversariante, empresa_aniversariante, whatsapp, data_envio, status, erro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            id, nome, empresa, whatsapp, datetime.now(),
            'success' if success else 'error',
            f"TESTE - {response}" if not success else "TESTE - Enviado com sucesso"
        ))
        
        conn.commit()
        conn.close()
        
        if success:
            return jsonify({'success': True, 'nome': nome, 'message': 'Mensagem de teste enviada!'})
        else:
            return jsonify({'success': False, 'message': f'Erro ao enviar: {response}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/delete/<int:id>', methods=['DELETE'])
def delete_aniversariante(id):
    """Exclui um aniversariante"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT nome FROM aniversariantes WHERE id = ?', (id,))
        aniversariante = cursor.fetchone()
        
        if not aniversariante:
            return jsonify({'success': False, 'message': 'Aniversariante não encontrado'})
        
        nome = aniversariante[0]
        
        # Exclui registros relacionados primeiro
        cursor.execute('DELETE FROM logs_aniversarios WHERE aniversariante_id = ?', (id,))
        cursor.execute('DELETE FROM aniversariantes WHERE id = ?', (id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Aniversariante {nome} excluído com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/aniversarios/logs')
def logs_aniversarios():
    """Lista logs de envio"""
    try:
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM logs_aniversarios 
            ORDER BY data_envio DESC 
            LIMIT 100
        ''')
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'aniversariante_id': row[1],
                'nome_aniversariante': row[2],
                'empresa_aniversariante': row[3],
                'whatsapp': row[4],
                'data_envio': row[5],
                'status': row[6],
                'erro': row[7]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    # Adicione esta rota no seu arquivo Python após as outras rotas de aniversários

@app.route('/api/aniversarios/add', methods=['POST'])
@login_requerido
def add_aniversariante():
    """Adiciona novo aniversariante diretamente no banco"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        # Validações obrigatórias
        nome = dados.get('nome', '').strip()
        nascimento = dados.get('nascimento', '').strip()
        whatsapp = dados.get('whatsapp', '').strip()
        
        if not all([nome, nascimento, whatsapp]):
            return jsonify({
                'success': False, 
                'message': 'Campos obrigatórios: nome, nascimento, whatsapp'
            }), 400
        
        # Dados opcionais
        empresa = dados.get('empresa', '').strip()
        ativo = dados.get('ativo', True)
        
        # Normaliza WhatsApp com mesma lógica da planilha
        whatsapp_clean = re.sub(r'\D', '', whatsapp)
        
        # Aplica regras de normalização brasileira
        if len(whatsapp_clean) == 10:
            # Formato antigo: adiciona 55 + 9
            ddd = whatsapp_clean[:2]
            numero = whatsapp_clean[2:]
            whatsapp_normalized = f"55{ddd}9{numero}"
        elif len(whatsapp_clean) == 11:
            # Formato atual: adiciona 55
            whatsapp_normalized = f"55{whatsapp_clean}"
        elif len(whatsapp_clean) == 12 and whatsapp_clean.startswith('55'):
            # Formato antigo internacional: adiciona 9
            whatsapp_normalized = f"{whatsapp_clean[:4]}9{whatsapp_clean[4:]}"
        elif len(whatsapp_clean) == 13 and whatsapp_clean.startswith('55'):
            # Já normalizado
            whatsapp_normalized = whatsapp_clean
        else:
            return jsonify({
                'success': False,
                'message': f'WhatsApp inválido: {whatsapp}. Use formato brasileiro: 21999999999'
            }), 400
        
        # Converte data
        try:
            # Se vier no formato brasileiro dd/mm/yyyy
            if '/' in nascimento:
                day, month, year = nascimento.split('/')
                nascimento_date = datetime(int(year), int(month), int(day)).date()
            else:
                # Se vier no formato yyyy-mm-dd do input date
                nascimento_date = datetime.strptime(nascimento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Data de nascimento inválida. Use formato dd/mm/yyyy ou yyyy-mm-dd'
            }), 400
        
        # Verifica duplicata (mesmo nome + nascimento)
        conn = sqlite3.connect('sistema.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM aniversariantes 
            WHERE UPPER(TRIM(nome)) = ? AND nascimento = ?
        ''', (nome.upper(), nascimento_date))
        
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Aniversariante já existe: {nome} ({nascimento_date})'
            }), 409
        
        # Insere novo registro
        cursor.execute('''
            INSERT INTO aniversariantes (nome, empresa, nascimento, whatsapp, ativo, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, empresa, nascimento_date, whatsapp_normalized, 1 if ativo else 0, datetime.now()))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Novo aniversariante adicionado: {nome} (ID: {new_id})")
        
        return jsonify({
            'success': True,
            'message': 'Aniversariante adicionado com sucesso!',
            'id': new_id,
            'nome': nome,
            'whatsapp_normalized': whatsapp_normalized
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar aniversariante: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500
# ===================== SCHEDULER AUTOMÁTICO =====================

def run_birthday_scheduler():
    """Executa o verificador automático de aniversários"""
    def job():
        try:
            config = get_birthday_config()
            if config.get('ativo', False):
                print(f"🎂 Executando verificação automática de aniversários...")
                # Simula uma requisição POST para check_today_birthdays
                with app.test_request_context('/api/aniversarios/check-today', method='POST'):
                    result = check_today_birthdays()
                    print(f"📧 Resultado: {result}")
        except Exception as e:
            print(f"❌ Erro no scheduler de aniversários: {e}")
    
    # Agenda para executar todos os dias no horário configurado
    while True:
        try:
            # Recarrega configuração a cada loop
            config = get_birthday_config()
            horario = config.get('horario_envio', '09:00')
            
            # Clear previous schedule
            schedule.clear()
            schedule.every().day.at(horario).do(job)
            
            print(f"⏰ Scheduler configurado para executar às {horario}")
            
            # Executa por 24 horas, depois recarrega config
            for _ in range(1440):  # 24 horas * 60 minutos
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
                
        except Exception as e:
            print(f"❌ Erro no scheduler: {e}")
            time.sleep(300)  # Espera 5 minutos antes de tentar novamente

def start_birthday_scheduler():
    """Inicia o scheduler em uma thread separada"""
    scheduler_thread = threading.Thread(target=run_birthday_scheduler, daemon=True)
    scheduler_thread.start()
    print("🚀 Scheduler de aniversários iniciado!")

# ===================== FUNÇÕES AUXILIARES =====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def auto_sync_on_startup():
    """Sincroniza automaticamente na inicialização se a planilha existir"""
    try:
        if os.path.exists(FIXED_SPREADSHEET):
            print(f"🔄 Sincronizando planilha fixa '{FIXED_SPREADSHEET}' na inicialização...")
            success, result = sync_from_fixed_spreadsheet()
            if success:
                print(f"✅ Planilha sincronizada com sucesso!")
                print(f"   📊 {result['imported_count']} novos registros")
                print(f"   🔄 {result['updated_count']} registros atualizados")
                if result['error_count'] > 0:
                    print(f"   ⚠️  {result['error_count']} erros encontrados")
                    for error in result['errors'][:3]:
                        print(f"      - {error}")
            else:
                print(f"❌ Erro na sincronização: {result}")
        else:
            print(f"📄 Planilha fixa '{FIXED_SPREADSHEET}' não encontrada.")
            print(f"   Coloque o arquivo na raiz do projeto ou faça upload via interface.")
    except Exception as e:
        print(f"❌ Erro na sincronização automática: {e}")

def test_excel_date_conversion():
    """Testa a conversão de datas do Excel"""
    print("\n🤖 Testando conversão de datas:")
    
    # Testa alguns valores seriais do Excel
    test_dates = [23762, 29610, 25232]  # Valores da sua planilha
    
    for excel_date in test_dates:
        converted = convert_excel_date(excel_date)
        print(f"   {excel_date} → {converted}")

# ===================== INICIALIZAÇÃO CORRIGIDA E COMPLETA =====================

def initialize_birthday_system():
    """Inicializa o sistema de aniversários"""
    print("\n🎂 ========= INICIALIZANDO SISTEMA DE ANIVERSÁRIOS =========")
    
    try:
        # Inicializa banco de dados
        print("📊 Inicializando banco de dados...")
        init_birthday_db()
        
        # Testa conversão de datas
        print("🔍 Testando conversão de datas...")
        test_excel_date_conversion()
        
        # Sincroniza planilha na inicialização
        print("📋 Verificando planilha de aniversários...")
        auto_sync_on_startup()
        
        # Inicia scheduler automático
        print("⏰ Iniciando scheduler automático...")
        start_birthday_scheduler()
        
        print("✅ Sistema de aniversários inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema de aniversários: {e}")
    
    print("========================================================\n")

def debug_spreadsheet():
    """Função para debugar a planilha"""
    try:
        if os.path.exists(FIXED_SPREADSHEET):
            print(f"\n🔍 DEBUGANDO PLANILHA: {FIXED_SPREADSHEET}")
            
            df = pd.read_excel(FIXED_SPREADSHEET)
            print(f"📊 Total de registros: {len(df)}")
            print(f"📋 Colunas: {list(df.columns)}")
            
            # Mostra primeiros 3 registros processados
            print("\n📝 Primeiros 3 registros processados:")
            for i, row in df.head(3).iterrows():
                nome = str(row['NOME']).strip()
                empresa = str(row.get('EMPRESA', '')).strip()
                whatsapp = clean_whatsapp(row['WHATSAPP'])
                nascimento = convert_excel_date(row['NASCIMENTO'])
                
                print(f"\n   Registro {i+1}:")
                print(f"   👤 Nome: {nome}")
                print(f"   🏢 Empresa: {empresa}")
                print(f"   📱 WhatsApp: {whatsapp}")
                print(f"   🎂 Nascimento: {row['NASCIMENTO']} → {nascimento}")
                
                if nascimento:
                    idade = calculate_age(nascimento)
                    print(f"   🎯 Idade: {idade} anos")
        else:
            print(f"📄 Planilha {FIXED_SPREADSHEET} não encontrada")
    except Exception as e:
        print(f"❌ Erro ao debugar planilha: {e}")

def setup_evolution_config():
    """Configura Evolution API na primeira execução"""
    config_file = 'evolution_config.json'
    
    try:
        if not os.path.exists(config_file):
            logger.warning(f"Arquivo {config_file} não encontrado. Criando com configurações padrão...")
            
            default_config = {
                "base_url": "http://82.25.69.24:8090",  # Usando seu IP atual
                "api_key": "MARCO_EVOLUTION_KEY_2024",
                "instance_name": "marco_reunioes_bot",
                "webhook_url": "http://82.25.69.24:3000/webhook/evolution",  # Webhook correto
                "phone_number": "5511999999999",
                "settings": {
                    "reject_call": False,
                    "msg_call": "Não posso atender chamadas no momento.",
                    "groups_ignore": True,
                    "always_online": True,
                    "read_messages": True,
                    "read_status": True
                },
                "database": {
                    "enabled": True,
                    "connection": {
                        "type": "sqlite",
                        "database": "./reunioes.db"  # Banco correto
                    }
                },
                "log_level": "INFO"
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Arquivo {config_file} criado")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao configurar Evolution API: {e}")
        return False

@app.route('/whatsapp/test-connection', methods=['POST'])
@login_requerido
def test_evolution_connection():
    """Testa conexão com Evolution API"""
    try:
        success, result = evolution_manager._make_request('GET', '/instance/fetchInstances')
        
        if success:
            return jsonify({
                "success": True,
                "message": "Conexão com Evolution API estabelecida",
                "api_url": evolution_manager.base_url,
                "instances": result
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Falha na conexão: {result.get('error', 'Erro desconhecido')}",
                "api_url": evolution_manager.base_url
            })
            
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}",
            "api_url": evolution_manager.base_url
        }), 500

@app.route('/config/verify')
@login_requerido
def verify_config():
    """Verifica configuração atual"""
    try:
        config_status = {
            "evolution_api": {
                "base_url": EVOLUTION_API_CONFIG['base_url'],
                "instance_name": EVOLUTION_API_CONFIG['instance_name'],
                "webhook_url": EVOLUTION_API_CONFIG['webhook_url'],
                "api_key_set": bool(EVOLUTION_API_CONFIG['api_key'] and EVOLUTION_API_CONFIG['api_key'] != 'YOUR_API_KEY_HERE')
            },
            "database": {
                "file_exists": os.path.exists(DATABASE),
                "path": os.path.abspath(DATABASE)
            },
            "config_file": {
                "exists": os.path.exists('evolution_config.json'),
                "path": os.path.abspath('evolution_config.json') if os.path.exists('evolution_config.json') else None
            }
        }
        
        return jsonify({
            "success": True,
            "config": config_status
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar configuração: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    """Endpoint de saúde MELHORADO com auto-correção"""
    try:
        # Verifica banco
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reunioes')
            total_meetings = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM reunioes 
                WHERE telefone_cliente IS NOT NULL 
                AND telefone_cliente != ''
                AND datetime(data_hora) >= datetime('now', '-7 days')
                AND status_confirmacao IN ('pending', 'unclear')
            ''')
            meetings_needing_monitor = cursor.fetchone()[0]
        
        # Verifica monitoramento
        monitoring_active = whatsapp_monitor.monitoring
        monitored_count = len(whatsapp_monitor.monitored_phones)
        
        # AUTO-CORREÇÃO: Se tem reuniões mas nada monitorado, tenta corrigir
        auto_corrected = False
        if meetings_needing_monitor > 0 and monitored_count == 0:
            logger.warning("⚠️ Reuniões sem monitoramento detectadas - auto-corrigindo...")
            try:
                auto_start_monitoring_on_startup()
                monitored_count = len(whatsapp_monitor.monitored_phones)
                auto_corrected = True
                logger.info(f"✅ Auto-correção realizada: {monitored_count} telefones agora monitorados")
            except Exception as e:
                logger.error(f"❌ Falha na auto-correção: {e}")
        
        # Verifica Evolution API (sem bloquear)
        evolution_status = "unknown"
        try:
            connected, _ = evolution_manager.check_connection_status()
            evolution_status = "connected" if connected else "disconnected"
        except:
            evolution_status = "error"
        
        return jsonify({
            "status": "healthy",
            "database": {
                "connected": True,
                "total_meetings": total_meetings,
                "meetings_needing_monitor": meetings_needing_monitor
            },
            "monitoring": {
                "active": monitoring_active,
                "phones_monitored": monitored_count,
                "auto_corrected": auto_corrected
            },
            "evolution_api": evolution_status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
    
#/*===================== ROTA DO CALENDÁRIO ===================== */   
@app.route('/calendario')
def calendario():
    """Rota para exibir o calendário com reuniões"""
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('reunioes.db')
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        cursor = conn.cursor()
        
        # Buscar todas as reuniões ordenadas por data
        cursor.execute('''
            SELECT 
                id,
                titulo,
                convidado,
                data_hora,
                assunto,
                nome_cliente,
                telefone_cliente,
                local_reuniao,
                link,
                confirmation_status,
                created_at
            FROM reunioes
            ORDER BY data_hora ASC
        ''')
        
        reunioes = cursor.fetchall()
        conn.close()
        
        # Converter para lista de dicionários para facilitar no JavaScript
        reunioes_list = []
        for reuniao in reunioes:
            reunioes_list.append({
                'id': reuniao['id'],
                'titulo': reuniao['titulo'],
                'convidado': reuniao['convidado'],
                'data_hora': reuniao['data_hora'],
                'assunto': reuniao['assunto'] or '',
                'nome_cliente': reuniao['nome_cliente'] or '',
                'telefone_cliente': reuniao['telefone_cliente'] or '',
                'local_reuniao': reuniao['local_reuniao'] or '',
                'link': reuniao['link'] or '',
                'confirmation_status': reuniao['confirmation_status'] or 'pending',
                'created_at': reuniao['created_at']
            })
        
        # Estatísticas para exibir (opcional)
        total_reunioes = len(reunioes_list)
        
        from datetime import datetime
        hoje = datetime.now().date()
        
        reunioes_hoje = sum(1 for r in reunioes_list 
                           if datetime.fromisoformat(r['data_hora']).date() == hoje)
        
        reunioes_futuras = sum(1 for r in reunioes_list 
                              if datetime.fromisoformat(r['data_hora']).date() > hoje)
        
        reunioes_passadas = sum(1 for r in reunioes_list 
                               if datetime.fromisoformat(r['data_hora']).date() < hoje)
        
        confirmadas = sum(1 for r in reunioes_list 
                         if r['confirmation_status'] == 'confirmed')
        
        pendentes = sum(1 for r in reunioes_list 
                       if r['confirmation_status'] == 'pending')
        
        recusadas = sum(1 for r in reunioes_list 
                       if r['confirmation_status'] == 'declined')
        
        stats = {
            'total': total_reunioes,
            'hoje': reunioes_hoje,
            'futuras': reunioes_futuras,
            'passadas': reunioes_passadas,
            'confirmadas': confirmadas,
            'pendentes': pendentes,
            'recusadas': recusadas
        }
        
        return render_template('calendario.html', 
                             reunioes=reunioes_list,
                             stats=stats)
        
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        # Em caso de erro, renderiza a página vazia
        return render_template('calendario.html', 
                             reunioes=[],
                             stats={
                                 'total': 0,
                                 'hoje': 0,
                                 'futuras': 0,
                                 'passadas': 0,
                                 'confirmadas': 0,
                                 'pendentes': 0,
                                 'recusadas': 0
                             })
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return render_template('calendario.html', 
                             reunioes=[],
                             stats={})
@app.route('/api/reunioes')
def api_reunioes():
    """API para retornar reuniões E EVENTOS em formato JSON para o calendário"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # ========== BUSCA REUNIÕES (🆕 ADICIONADO numero_pessoas) ==========
        cursor.execute('''
            SELECT 
                id,
                titulo,
                convidado,
                data_hora,
                assunto,
                nome_cliente,
                telefone_cliente,
                local_reuniao,
                link,
                status_confirmacao,
                numero_pessoas
            FROM reunioes
            ORDER BY data_hora ASC
        ''')
        
        reunioes = cursor.fetchall()
        
        # ========== BUSCA EVENTOS ==========
        cursor.execute('''
            SELECT 
                id,
                titulo,
                tipo,
                data_inicio,
                data_fim,
                local,
                descricao,
                participantes,
                cor
            FROM eventos
            ORDER BY data_inicio ASC
        ''')
        
        eventos = cursor.fetchall()
        conn.close()
        
        # Converte reuniões (🆕 ADICIONADO numero_pessoas no dicionário)
        reunioes_list = []
        for reuniao in reunioes:
            reunioes_list.append({
                'id': reuniao[0],
                'tipo_item': 'reuniao',
                'titulo': reuniao[1],
                'convidado': reuniao[2],
                'data_hora': reuniao[3],
                'assunto': reuniao[4] or '',
                'nome_cliente': reuniao[5] or '',
                'telefone_cliente': reuniao[6] or '',
                'local_reuniao': reuniao[7] or '',
                'link': reuniao[8] or '',
                'confirmation_status': reuniao[9] or 'pending',
                'numero_pessoas': reuniao[10] if len(reuniao) > 10 and reuniao[10] is not None else None  # 🆕 ADICIONE ESTA LINHA
            })
        
        # Converte eventos
        eventos_list = []
        for evento in eventos:
            eventos_list.append({
                'id': evento[0],
                'tipo_item': 'evento',
                'titulo': evento[1],
                'tipo': evento[2],
                'data_inicio': evento[3],
                'data_fim': evento[4],
                'local': evento[5] or '',
                'descricao': evento[6] or '',
                'participantes': evento[7] or '',
                'cor': evento[8] or 'amarelo'
            })
        
        # RETORNA AMBOS
        return jsonify({
            'reunioes': reunioes_list,
            'eventos': eventos_list
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados para API: {e}")
        return jsonify({
            'reunioes': [],
            'eventos': []
        }), 500
    
#ROTAS ADICIONAIS
@app.route('/api/meetings/recent-updates', methods=['GET'])
@login_requerido
def api_meetings_recent_updates():
    """
    Retorna atualizações recentes das reuniões (fallback para polling)
    """
    try:
        # Busca reuniões atualizadas nos últimos 5 minutos
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id,
                    titulo,
                    status_confirmacao,
                    data_hora,
                    updated_at
                FROM reunioes
                WHERE updated_at >= ?
                ORDER BY updated_at DESC
                LIMIT 20
            ''', (five_minutes_ago.isoformat(),))
            
            updates = []
            for row in cursor.fetchall():
                updates.append({
                    'meeting_id': row['id'],
                    'title': row['titulo'],
                    'status': row['status_confirmacao'],
                    'datetime': row['data_hora'],
                    'updated_at': row['updated_at']
                })
            
            return jsonify({
                'success': True,
                'updates': updates,
                'count': len(updates)
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar atualizações: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'updates': []
        }), 200  # Retorna 200 para não quebrar frontend

# ===============================
# === ROTAS DE EVENTOS ==========
# ===============================

@app.route('/api/eventos/list', methods=['GET'])
@login_requerido
def api_eventos_list():
    """Lista todos os eventos"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    id, titulo, tipo, data_inicio, data_fim, 
                    local, descricao, participantes, cor, 
                    created_at, updated_at
                FROM eventos
                ORDER BY data_inicio ASC
            ''')
            
            eventos = cursor.fetchall()
            
            eventos_list = []
            for evento in eventos:
                eventos_list.append({
                    'id': evento[0],
                    'titulo': evento[1],
                    'tipo': evento[2],
                    'data_inicio': evento[3],
                    'data_fim': evento[4],
                    'local': evento[5] or '',
                    'descricao': evento[6] or '',
                    'participantes': evento[7] or '',
                    'cor': evento[8] or 'amarelo',
                    'created_at': evento[9],
                    'updated_at': evento[10]
                })
            
            logger.info(f"📅 Listando {len(eventos_list)} eventos")
            
            return jsonify({
                'success': True,
                'eventos': eventos_list,
                'total': len(eventos_list)
            })
            
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao listar eventos: {str(e)}',
            'eventos': []
        }), 500


@app.route('/api/eventos/criar', methods=['POST'])
@login_requerido
def api_eventos_criar():
    """Cria um novo evento"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        # Validações obrigatórias
        titulo = dados.get('titulo', '').strip()
        tipo = dados.get('tipo', '').strip()
        data_inicio = dados.get('data_inicio', '').strip()
        data_fim = dados.get('data_fim', '').strip()
        
        if not all([titulo, tipo, data_inicio, data_fim]):
            return jsonify({
                'success': False,
                'message': 'Campos obrigatórios: titulo, tipo, data_inicio, data_fim'
            }), 400
        
        # Valida datas
        try:
            dt_inicio = parser.parse(data_inicio)
            dt_fim = parser.parse(data_fim)
            
            if dt_fim < dt_inicio:
                return jsonify({
                    'success': False,
                    'message': 'Data de término deve ser posterior à data de início'
                }), 400
                
        except Exception:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido'
            }), 400
        
        # Dados opcionais
        local = dados.get('local', '').strip()
        descricao = dados.get('descricao', '').strip()
        participantes = dados.get('participantes', '').strip()
        cor = dados.get('cor', 'amarelo').strip()
        
        # Valida tipo
        tipos_validos = ['viagem', 'feira', 'conferencia', 'treinamento', 'evento_interno', 'outro']
        if tipo not in tipos_validos:
            return jsonify({
                'success': False,
                'message': f'Tipo inválido. Use: {", ".join(tipos_validos)}'
            }), 400
        
        # Valida cor
        cores_validas = ['amarelo', 'laranja', 'verde', 'azul', 'roxo']
        if cor not in cores_validas:
            cor = 'amarelo'
        
        # Insere no banco
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO eventos 
                (titulo, tipo, data_inicio, data_fim, local, descricao, participantes, cor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (titulo, tipo, data_inicio, data_fim, local, descricao, participantes, cor))
            
            evento_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"✅ Evento criado: ID {evento_id} - {titulo}")
        
        return jsonify({
            'success': True,
            'message': 'Evento criado com sucesso!',
            'evento_id': evento_id
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao criar evento: {str(e)}'
        }), 500


@app.route('/api/eventos/editar/<int:evento_id>', methods=['PUT'])
@login_requerido
def api_eventos_editar(evento_id):
    """Edita um evento existente"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        # Verifica se evento existe
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM eventos WHERE id = ?', (evento_id,))
            
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Evento não encontrado'
                }), 404
            
            # Validações
            titulo = dados.get('titulo', '').strip()
            tipo = dados.get('tipo', '').strip()
            data_inicio = dados.get('data_inicio', '').strip()
            data_fim = dados.get('data_fim', '').strip()
            
            if not all([titulo, tipo, data_inicio, data_fim]):
                return jsonify({
                    'success': False,
                    'message': 'Campos obrigatórios não podem estar vazios'
                }), 400
            
            # Valida datas
            try:
                dt_inicio = parser.parse(data_inicio)
                dt_fim = parser.parse(data_fim)
                
                if dt_fim < dt_inicio:
                    return jsonify({
                        'success': False,
                        'message': 'Data de término deve ser posterior à data de início'
                    }), 400
                    
            except Exception:
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido'
                }), 400
            
            # Dados opcionais
            local = dados.get('local', '').strip()
            descricao = dados.get('descricao', '').strip()
            participantes = dados.get('participantes', '').strip()
            cor = dados.get('cor', 'amarelo').strip()
            
            # Atualiza
            cursor.execute('''
                UPDATE eventos
                SET titulo = ?, tipo = ?, data_inicio = ?, data_fim = ?,
                    local = ?, descricao = ?, participantes = ?, cor = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (titulo, tipo, data_inicio, data_fim, local, descricao, participantes, cor, evento_id))
            
            conn.commit()
        
        logger.info(f"✅ Evento atualizado: ID {evento_id}")
        
        return jsonify({
            'success': True,
            'message': 'Evento atualizado com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao editar evento: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao editar evento: {str(e)}'
        }), 500


@app.route('/api/eventos/excluir/<int:evento_id>', methods=['DELETE'])
@login_requerido
def api_eventos_excluir(evento_id):
    """Exclui um evento"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Verifica se existe
            cursor.execute('SELECT titulo FROM eventos WHERE id = ?', (evento_id,))
            evento = cursor.fetchone()
            
            if not evento:
                return jsonify({
                    'success': False,
                    'message': 'Evento não encontrado'
                }), 404
            
            titulo = evento[0]
            
            # Exclui
            cursor.execute('DELETE FROM eventos WHERE id = ?', (evento_id,))
            conn.commit()
        
        logger.info(f"🗑️ Evento excluído: ID {evento_id} - {titulo}")
        
        return jsonify({
            'success': True,
            'message': f'Evento "{titulo}" excluído com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao excluir evento: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir evento: {str(e)}'
        }), 500


@app.route('/api/eventos/get/<int:evento_id>', methods=['GET'])
@login_requerido
def api_eventos_get(evento_id):
    """Obtém detalhes de um evento específico"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    id, titulo, tipo, data_inicio, data_fim,
                    local, descricao, participantes, cor,
                    created_at, updated_at
                FROM eventos
                WHERE id = ?
            ''', (evento_id,))
            
            evento = cursor.fetchone()
            
            if not evento:
                return jsonify({
                    'success': False,
                    'message': 'Evento não encontrado'
                }), 404
            
            evento_dict = {
                'id': evento[0],
                'titulo': evento[1],
                'tipo': evento[2],
                'data_inicio': evento[3],
                'data_fim': evento[4],
                'local': evento[5] or '',
                'descricao': evento[6] or '',
                'participantes': evento[7] or '',
                'cor': evento[8] or 'amarelo',
                'created_at': evento[9],
                'updated_at': evento[10]
            }
            
            return jsonify({
                'success': True,
                'evento': evento_dict
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar evento: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar evento: {str(e)}'
        }), 500
    
@app.route('/api/meetings/<int:meeting_id>/status', methods=['GET'])
@login_requerido
def api_meeting_status(meeting_id):
    """
    Retorna status de uma reunião específica
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id,
                    titulo,
                    convidado,
                    status_confirmacao,
                    telefone_cliente,
                    data_hora
                FROM reunioes
                WHERE id = ?
            ''', (meeting_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Reunião não encontrada'
                }), 404
            
            meeting = {
                'id': row['id'],
                'title': row['titulo'],
                'convidado': row['convidado'],
                'status_confirmacao': row['status_confirmacao'],
                'phone': row['telefone_cliente'],
                'datetime': row['data_hora']
            }
            
            return jsonify({
                'success': True,
                'meeting': meeting
            })
            
    except Exception as e:
        logger.error(f"Erro ao buscar status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/eventos/<int:evento_id>', methods=['GET'])
def get_evento(evento_id):
    """Busca dados de um evento específico"""
    try:
        conn = sqlite3.connect(REUNIOES_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM eventos WHERE id = ?
        ''', (evento_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            evento = dict(row)
            return jsonify({
                'success': True,
                'evento': evento
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Evento não encontrado'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao buscar evento {evento_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
#/*===================== ROTA DO CALENDÁRIO ===================== */ 
# ===================== FUNÇÃO DE ENVIO DE ANIVERSÁRIOS SIMPLIFICADA =====================

def send_birthday_whatsapp_message(phone, message):
    """Envia mensagem via Evolution API para sistema de aniversários - VERSÃO SIMPLIFICADA"""
    try:
        # Usa o manager global em vez de duplicar código
        success, response = evolution_manager.send_message(phone, message)
        return success, response
    except Exception as e:
        logger.error(f"Erro no envio de aniversário: {e}")
        return False, str(e)

# ===================== INICIALIZAÇÃO PRINCIPAL COMPLETA =====================
def auto_start_monitoring_on_startup():
    """
    Inicia monitoramento automaticamente na inicialização
    Adiciona todas as reuniões ativas ao monitoramento
    """
    try:
        logger.info("🚀 Iniciando auto-monitoramento na startup...")
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Busca reuniões que precisam ser monitoradas
            cursor.execute('''
                SELECT id, titulo, telefone_cliente, status_confirmacao
                FROM reunioes 
                WHERE telefone_cliente IS NOT NULL 
                AND telefone_cliente != ''
                AND datetime(data_hora) >= datetime('now', '-7 days')
                AND datetime(data_hora) <= datetime('now', '+30 days')
                AND status_confirmacao IN ('pending', 'unclear')
            ''')
            
            meetings = cursor.fetchall()
            monitored_count = 0
            
            for meeting_id, titulo, telefone, status in meetings:
                try:
                    normalized_phone = evolution_manager.normalize_phone_number(telefone)
                    whatsapp_monitor.add_phone_to_monitor(normalized_phone, meeting_id)
                    monitored_count += 1
                    logger.info(f"📱 Auto-monitorando: {titulo[:30]}... ({status})")
                except Exception as e:
                    logger.error(f"❌ Erro ao adicionar {telefone}: {e}")
            
            # Inicia monitoramento se houver telefones
            if monitored_count > 0:
                if not whatsapp_monitor.monitoring:
                    whatsapp_monitor.start_monitoring()
                logger.info(f"✅ Auto-monitoramento ativado: {monitored_count} telefones")
            else:
                logger.info("ℹ️ Nenhuma reunião pendente para monitorar")
                
    except Exception as e:
        logger.error(f"❌ Erro no auto-monitoramento: {e}")

if __name__ == '__main__':
    logger.info("🚀 Inicializando aplicação com Evolution API...")
    
    try:
        # 1. Configuração inicial
        logger.info("⚙️ Verificando configurações...")
        setup_evolution_config()
        
        # 2. Inicializa banco de dados principal
        logger.info("📊 Inicializando banco de dados de reuniões...")
        init_db()
        
        # 3. Inicializa banco de aniversários
        logger.info("🎂 Inicializando banco de aniversários...")
        init_birthday_db()
        
        # 4. Inicia sistema de aniversários completo
        logger.info("🎉 Inicializando sistema de aniversários...")
        initialize_birthday_system()
        
        # 5. Inicia monitoramento WhatsApp
        logger.info("📱 Ativando monitoramento WhatsApp...")
        whatsapp_monitor.start_monitoring()
        
        # 🆕 ADICIONE ESTA LINHA AQUI:
        auto_start_monitoring_on_startup()
        
        # 6. Verifica conexão Evolution API
        logger.info("🔗 Verificando conexão com Evolution API...")
        try:
            connected, status = evolution_manager.check_connection_status()
            if connected:
                logger.info(f"✅ Evolution API conectada: {status}")
            else:
                logger.warning(f"⚠️ Evolution API não conectada: {status}")
                logger.info("💡 Você pode conectar via interface web após iniciar")
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível verificar Evolution API: {e}")
        
        # 7. Inicia threads de background
        logger.info("🔄 Iniciando processos em background...")
        
        # Thread para verificar reuniões futuras
        try:
            background_thread = threading.Thread(target=verificar_reunioes_futuras, daemon=True)
            background_thread.start()
            logger.info("✅ Thread de verificação de reuniões iniciada")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao iniciar thread de reuniões: {e}")
        
        # Thread para limpeza de logs
        try:
            cleanup_thread = threading.Thread(target=cleanup_old_logs, daemon=True)
            cleanup_thread.start()
            logger.info("✅ Thread de limpeza de logs iniciada")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao iniciar thread de limpeza: {e}")
        
        # 8. Informações do sistema
        logger.info("=" * 70)
        logger.info("🎉 APLICAÇÃO INICIALIZADA COM SUCESSO!")
        logger.info("=" * 70)
        logger.info(f"🌐 Servidor: http://0.0.0.0:3000")
        logger.info(f"🏠 Aplicação: http://localhost:3000")
        logger.info(f"🏠 Aplicação Externa: http://82.25.69.24:3000")
        logger.info(f"📋 Agenda: http://localhost:3000/agenda")
        logger.info(f"🎂 Aniversários: http://localhost:3000/disparador")
        logger.info(f"❤️ Health Check: http://localhost:3000/health")
        logger.info(f"📱 Monitoramento: {'ATIVO' if whatsapp_monitor.monitoring else 'INATIVO'}")
        logger.info(f"🤖 Evolution API: {evolution_manager.base_url}")
        logger.info(f"📞 Webhook: {EVOLUTION_API_CONFIG['webhook_url']}")
        logger.info(f"🔑 Instância: {EVOLUTION_API_CONFIG['instance_name']}")
        logger.info("=" * 70)
        
        # 9. Debug da planilha (opcional)
        if os.path.exists(FIXED_SPREADSHEET):
            logger.info("🔍 Executando debug da planilha...")
            debug_spreadsheet()
        
        # 10. INICIA O SERVIDOR FLASK
        logger.info("🚀 Iniciando servidor Flask na porta 3000...")
        app.run(
            debug=False,      # Produção para evitar recarregamento
            host='0.0.0.0',   # Aceita conexões externas
            port=3000,        # Porta 3000 (conforme webhook)
            threaded=True,    # Permite múltiplas conexões simultâneas
            use_reloader=False  # Evita reinicialização dupla
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Aplicação interrompida pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 ERRO CRÍTICO na inicialização:")
        logger.error(f"   {str(e)}")
        logger.error("🔍 Verifique os logs acima para identificar o problema")
        import traceback
        logger.error(f"📋 Traceback completo:\n{traceback.format_exc()}")
        exit(1)
    finally:
        logger.info("👋 Encerrando aplicação...")

# ===================== INSTRUÇÕES DE USO ATUALIZADAS =====================
