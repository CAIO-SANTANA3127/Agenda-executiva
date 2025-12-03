#!/usr/bin/env python3
"""
TESTADOR COMPLETO DA EVOLUTION API
Arquivo: test_evolution_api.py

Este script testa sua Evolution API e identifica problemas
Execute: python test_evolution_api.py
"""

import requests
import json
import time
from datetime import datetime
import sys

# CONFIGURAÇÕES - ATUALIZE COM SEUS DADOS
EVOLUTION_CONFIG = {
    'base_url': 'http://82.25.69.24:8090',
    'api_key': 'olvjg1k1ldmbhyl8owi6',  # API Key correta do Evolution Manager
    'instance_name': 'marco_reunioes_bot',
    'webhook_url': 'http://82.25.69.24:3000/webhook/evolution'
}

# TELEFONE PARA TESTE (use seu próprio número)
TEST_PHONE = '5521982161008'  # Seu número da imagem anterior

class EvolutionAPITester:
    def __init__(self, config):
        self.config = config
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.instance_name = config['instance_name']
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'apikey': self.api_key,
            'Accept': 'application/json'
        })
        
        print("=" * 60)
        print("🧪 TESTADOR EVOLUTION API")
        print("=" * 60)
        print(f"🔗 Base URL: {self.base_url}")
        print(f"🔑 API Key: {self.api_key[:8]}...")
        print(f"📱 Instância: {self.instance_name}")
        print(f"📞 Telefone teste: {TEST_PHONE}")
        print("=" * 60)

    def log_test(self, test_name, success=None, details=""):
        """Log formatado dos testes"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = ""
        if success is True:
            status = "✅ PASSOU"
        elif success is False:
            status = "❌ FALHOU"
        else:
            status = "🔍 TESTANDO"
        
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"          💬 {details}")

    def make_request(self, method, endpoint, data=None, timeout=10):
        """Faz requisição HTTP com logs detalhados"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            kwargs = {'timeout': timeout}
            if method.upper() in ['POST', 'PUT'] and data:
                kwargs['json'] = data
            elif method.upper() == 'GET' and data:
                kwargs['params'] = data

            response = getattr(self.session, method.lower())(url, **kwargs)
            
            return {
                'success': response.status_code in [200, 201],
                'status_code': response.status_code,
                'response': response.text,
                'json': response.json() if response.text and response.text.strip() else {},
                'url': url
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout na requisição'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Erro de conexão'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_1_api_connection(self):
        """Teste 1: Conexão básica com a API"""
        self.log_test("1. Conexão básica com API")
        
        result = self.make_request('GET', '/manager/fetchInstances')
        
        if result['success']:
            self.log_test("1. Conexão básica", True, f"Status {result['status_code']}")
            return True, result['json']
        else:
            error = result.get('error', f"HTTP {result.get('status_code', 'unknown')}")
            self.log_test("1. Conexão básica", False, error)
            return False, error

    def test_2_instance_exists(self, instances_data):
        """Teste 2: Verifica se instância existe"""
        self.log_test("2. Verificação de instância existente")
        
        if not instances_data or not isinstance(instances_data, list):
            self.log_test("2. Instância existe", False, "Dados de instâncias inválidos")
            return False, "Dados inválidos"
        
        found_instance = None
        for instance in instances_data:
            # Múltiplas formas de buscar o nome
            possible_names = [
                instance.get('instance', {}).get('instanceName'),
                instance.get('instanceName'),
                instance.get('name')
            ]
            
            for name in possible_names:
                if name == self.instance_name:
                    found_instance = instance
                    break
            
            if found_instance:
                break
        
        if found_instance:
            state = found_instance.get('instance', {}).get('state', 'unknown')
            self.log_test("2. Instância existe", True, f"Estado: {state}")
            return True, found_instance
        else:
            available = [inst.get('instance', {}).get('instanceName', 'unknown') for inst in instances_data]
            self.log_test("2. Instância existe", False, f"Não encontrada. Disponíveis: {available}")
            return False, "Instância não encontrada"

    def test_3_connection_state(self):
        """Teste 3: Estado da conexão da instância"""
        self.log_test("3. Estado da conexão")
        
        result = self.make_request('GET', f'/instance/connectionState/{self.instance_name}')
        
        if result['success']:
            state = result['json'].get('state', 'unknown')
            self.log_test("3. Estado conexão", True, f"Estado: {state}")
            return True, state
        else:
            error = result.get('error', f"HTTP {result.get('status_code')}")
            self.log_test("3. Estado conexão", False, error)
            return False, error

    def test_4_qr_code(self):
        """Teste 4: Obtenção de QR Code"""
        self.log_test("4. Obtenção de QR Code")
        
        result = self.make_request('GET', f'/instance/qrcode/{self.instance_name}')
        
        if result['success']:
            qr_data = result['json']
            has_qr = bool(qr_data.get('qrcode') or qr_data.get('base64'))
            self.log_test("4. QR Code", True, f"QR disponível: {has_qr}")
            return True, qr_data
        else:
            error = result.get('error', f"HTTP {result.get('status_code')}")
            self.log_test("4. QR Code", False, error)
            return False, error

    def test_5_send_message(self):
        """Teste 5: Envio de mensagem"""
        self.log_test("5. Envio de mensagem de teste")
        
        # Múltiplos formatos para testar
        formats = [
            {
                "name": "Formato v2.x textMessage",
                "data": {
                    "number": TEST_PHONE,
                    "textMessage": {
                        "text": f"🧪 TESTE EVOLUTION API - {datetime.now().strftime('%H:%M:%S')}"
                    }
                }
            },
            {
                "name": "Formato v1.x text",
                "data": {
                    "number": TEST_PHONE,
                    "text": f"🧪 TESTE EVOLUTION API - {datetime.now().strftime('%H:%M:%S')}"
                }
            }
        ]
        
        for fmt in formats:
            self.log_test(f"5. Testando {fmt['name']}")
            
            result = self.make_request('POST', f'/message/sendText/{self.instance_name}', fmt['data'])
            
            if result['success']:
                self.log_test("5. Envio mensagem", True, f"Sucesso com {fmt['name']}")
                return True, result['json']
            else:
                error = result.get('error', f"HTTP {result.get('status_code')}")
                self.log_test(f"5. {fmt['name']}", False, error)
        
        self.log_test("5. Envio mensagem", False, "Todos os formatos falharam")
        return False, "Falha em todos os formatos"

    def test_6_restart_instance(self):
        """Teste 6: Reinicialização da instância"""
        self.log_test("6. Reinicialização de instância")
        
        result = self.make_request('PUT', f'/instance/restart/{self.instance_name}')
        
        if result['success']:
            self.log_test("6. Restart instância", True, "Reinicialização iniciada")
            return True, result['json']
        else:
            error = result.get('error', f"HTTP {result.get('status_code')}")
            self.log_test("6. Restart instância", False, error)
            return False, error

    def test_7_user_info(self):
        """Teste 7: Informações do usuário"""
        self.log_test("7. Informações do usuário")
        
        result = self.make_request('GET', f'/chat/whatsappNumbers/{self.instance_name}')
        
        if result['success']:
            user_data = result['json']
            self.log_test("7. Info usuário", True, f"Dados obtidos: {len(str(user_data))} chars")
            return True, user_data
        else:
            error = result.get('error', f"HTTP {result.get('status_code')}")
            self.log_test("7. Info usuário", False, error)
            return False, error

    def run_comprehensive_test(self):
        """Executa todos os testes em sequência"""
        print(f"\n🚀 Iniciando testes em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("-" * 60)
        
        test_results = {}
        
        # Teste 1: Conexão API
        success, data = self.test_1_api_connection()
        test_results['api_connection'] = success
        if not success:
            print("\n💥 ERRO CRÍTICO: Não foi possível conectar com a API")
            print(f"   ➤ Verifique se a Evolution API está rodando em {self.base_url}")
            print(f"   ➤ Verifique se a API Key '{self.api_key}' está correta")
            return test_results
        
        instances_data = data
        
        # Teste 2: Instância existe
        success, instance_data = self.test_2_instance_exists(instances_data)
        test_results['instance_exists'] = success
        if not success:
            print(f"\n⚠️ AVISO: Instância '{self.instance_name}' não encontrada")
            print("   ➤ Crie a instância manualmente no Evolution Manager")
            return test_results
        
        # Teste 3: Estado da conexão
        success, state = self.test_3_connection_state()
        test_results['connection_state'] = success
        
        # Teste 4: QR Code
        success, qr_data = self.test_4_qr_code()
        test_results['qr_code'] = success
        
        # Teste 5: Envio de mensagem (só se conectado)
        if state == 'open':
            success, msg_data = self.test_5_send_message()
            test_results['send_message'] = success
        else:
            self.log_test("5. Envio mensagem", None, f"Pulado - Estado: {state}")
            test_results['send_message'] = None
        
        # Teste 6: Restart (opcional)
        if input("\n❓ Deseja testar reinicialização da instância? (s/N): ").lower() == 's':
            success, restart_data = self.test_6_restart_instance()
            test_results['restart'] = success
        
        # Teste 7: Info do usuário
        success, user_data = self.test_7_user_info()
        test_results['user_info'] = success
        
        return test_results

    def print_summary(self, results):
        """Imprime resumo dos testes"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        total_tests = len([r for r in results.values() if r is not None])
        passed_tests = len([r for r in results.values() if r is True])
        
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"❌ Testes falharam: {len([r for r in results.values() if r is False])}")
        print(f"⏭️ Testes pulados: {len([r for r in results.values() if r is None])}")
        print(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n🔍 DETALHES:")
        test_names = {
            'api_connection': 'Conexão com API',
            'instance_exists': 'Instância existe',
            'connection_state': 'Estado da conexão',
            'qr_code': 'Obtenção QR Code',
            'send_message': 'Envio de mensagem',
            'restart': 'Reinicialização',
            'user_info': 'Info do usuário'
        }
        
        for key, result in results.items():
            name = test_names.get(key, key)
            if result is True:
                status = "✅ PASSOU"
            elif result is False:
                status = "❌ FALHOU"
            else:
                status = "⏭️ PULADO"
            
            print(f"   {status} {name}")
        
        print("\n💡 PRÓXIMOS PASSOS:")
        if not results.get('api_connection'):
            print("   1. Verifique se Evolution API está rodando")
            print("   2. Confirme a API Key no Evolution Manager")
            print("   3. Teste conectividade de rede")
        elif not results.get('instance_exists'):
            print("   1. Crie a instância no Evolution Manager")
            print("   2. Configure o webhook se necessário")
        elif results.get('connection_state') and results.get('qr_code'):
            print("   1. Escaneie o QR Code no WhatsApp")
            print("   2. Aguarde a conexão ser estabelecida")
        elif results.get('send_message') is False:
            print("   1. Verifique se WhatsApp está conectado")
            print("   2. Confirme formato das mensagens")
        else:
            print("   🎉 Sua Evolution API está funcionando!")

def main():
    """Função principal"""
    try:
        print("Pressione Ctrl+C a qualquer momento para interromper\n")
        
        tester = EvolutionAPITester(EVOLUTION_CONFIG)
        results = tester.run_comprehensive_test()
        tester.print_summary(results)
        
        print(f"\n✨ Teste concluído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()