"""
=================================================
INTEGRAÇÃO DO WEBHOOK PRINCIPAL COM API REALTIME
=================================================
Notifica a API de tempo real quando houver mudanças
"""

import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Configuração da API de tempo real
REALTIME_API_URL = 'http://localhost:5001'

class RealtimeAPINotifier:
    """Notifica a API de tempo real sobre mudanças"""
    
    @staticmethod
    def notify_meeting_update(meeting_id: int, update_type: str = 'status_change', triggered_by: str = 'system') -> bool:
        """
        Notifica a API de tempo real sobre atualização de reunião
        
        Args:
            meeting_id: ID da reunião
            update_type: Tipo de atualização ('status_change', 'new_response', 'manual_update')
            triggered_by: Quem disparou ('webhook', 'system', 'user')
        
        Returns:
            bool: True se notificação foi enviada com sucesso
        """
        try:
            url = f"{REALTIME_API_URL}/webhook/meeting-update"
            
            payload = {
                'meeting_id': meeting_id,
                'update_type': update_type,
                'triggered_by': triggered_by
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📡 Notificação enviada para API realtime: Reunião {meeting_id}")
                return data.get('success', False)
            else:
                logger.warning(f"⚠️ Falha ao notificar API realtime: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout ao notificar API realtime (reunião {meeting_id})")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 API realtime não disponível (reunião {meeting_id})")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao notificar API realtime: {e}")
            return False

# =================================================
# FUNÇÕES DE INTEGRAÇÃO
# =================================================

def notify_on_status_change(meeting_id: int) -> None:
    """Notifica quando status da reunião muda"""
    RealtimeAPINotifier.notify_meeting_update(
        meeting_id,
        update_type='status_change',
        triggered_by='webhook'
    )

def notify_on_new_response(meeting_id: int) -> None:
    """Notifica quando há nova resposta do cliente"""
    RealtimeAPINotifier.notify_meeting_update(
        meeting_id,
        update_type='new_response',
        triggered_by='webhook'
    )

def notify_on_manual_update(meeting_id: int) -> None:
    """Notifica quando usuário atualiza manualmente"""
    RealtimeAPINotifier.notify_meeting_update(
        meeting_id,
        update_type='manual_update',
        triggered_by='user'
    )


# =================================================
# MODIFICAÇÕES NO CÓDIGO EXISTENTE
# =================================================

# ADICIONE ESTAS LINHAS NOS SEGUINTES LUGARES:

"""
1. Na função update_meeting_status() - linha ~1234 do seu código:
   
   def update_meeting_status(meeting_id: int, status: str):
       try:
           # ... código existente ...
           
           conn.commit()
           
           # 🆕 ADICIONE ESTA LINHA:
           notify_on_status_change(meeting_id)
           
           return True
       except Exception as e:
           # ... código existente ...


2. Na função save_client_response() - linha ~1180 do seu código:
   
   def save_client_response(meeting_id: int, response_text: str, ...):
       try:
           # ... código existente ...
           
           conn.commit()
           
           # 🆕 ADICIONE ESTA LINHA:
           notify_on_new_response(meeting_id)
           
       except Exception as e:
           # ... código existente ...


3. Na rota @app.route('/agenda/manual-confirmation/<int:meeting_id>', ...):
   
   @app.route('/agenda/manual-confirmation/<int:meeting_id>', methods=['POST'])
   @login_requerido
   def manual_confirmation(meeting_id):
       try:
           # ... código existente ...
           
           # 🆕 ADICIONE ESTA LINHA ANTES DO RETURN:
           notify_on_manual_update(meeting_id)
           
           return jsonify({
               'success': True,
               'message': f'Status da reunião atualizado para: {status}'
           })
       except Exception as e:
           # ... código existente ...


4. No método process_webhook_message() da classe WhatsAppMonitor:
   
   def process_webhook_message(self, webhook_data: Dict) -> bool:
       try:
           # ... código existente ...
           
           if success:
               logger.info(f"✅ Reunião {meeting_id} atualizada para: {analysis['status']}")
               
               # 🆕 ADICIONE ESTA LINHA:
               notify_on_status_change(meeting_id)
               
               if analysis['status'] in ['confirmed', 'declined']:
                   self._remove_from_monitoring(meeting_id)
           
           return True
       except Exception as e:
           # ... código existente ...
"""

print("""
=================================================
INTEGRAÇÃO COM API DE TEMPO REAL
=================================================

Para ativar notificações em tempo real:

1. Inicie a API de tempo real:
   python webhook_realtime_api.py

2. Adicione as chamadas de notificação no código principal
   (veja instruções acima)

3. Inclua o cliente JavaScript no seu HTML:
   <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
   <script src="/static/js/realtime_client.js"></script>

4. Para monitorar uma reunião específica:
   realtimeClient.subscribeMeeting(meetingId);

=================================================
""")