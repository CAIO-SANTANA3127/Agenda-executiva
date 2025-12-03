#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SCRIPT DE TESTE COMPLETO PARA WEBHOOK
Testa todas as etapas do processamento de respostas do WhatsApp
"""

import requests
import json
import sqlite3
from datetime import datetime
import time

# ====================================
# CONFIGURAÇÕES (ajuste se necessário)
# ====================================
BASE_URL = "http://localhost:3000"  # URL do seu servidor Flask
YOUR_PHONE = "5521982161008"  # ← SEU NÚMERO REAL
TEST_INSTANCE = "marco_reunioes_bot"  # Nome da instância
API_KEY = "olvjg1k1ldmbhyl8owi6"  # Sua API key

# ====================================
# CORES PARA TERMINAL
# ====================================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# ====================================
# TESTES INDIVIDUAIS
# ====================================

def test_1_server_health():
    """Teste 1: Servidor está rodando?"""
    print_header("TESTE 1: Verificando Servidor Flask")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Servidor está rodando!")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Database: {data.get('database')}")
            print_info(f"Monitoring: {data.get('monitoring')}")
            return True
        else:
            print_error(f"Servidor retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Não foi possível conectar ao servidor!")
        print_warning(f"Certifique-se de que o Flask está rodando em {BASE_URL}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

def test_2_database_check():
    """Teste 2: Banco de dados tem reuniões?"""
    print_header("TESTE 2: Verificando Banco de Dados")
    
    try:
        conn = sqlite3.connect('reunioes.db')
        cursor = conn.cursor()
        
        # Verifica se tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reunioes'")
        if not cursor.fetchone():
            print_error("Tabela 'reunioes' não existe!")
            return False
        
        # Conta reuniões
        cursor.execute("SELECT COUNT(*) FROM reunioes")
        total_reunioes = cursor.fetchone()[0]
        print_info(f"Total de reuniões: {total_reunioes}")
        
        # Reuniões com telefone
        cursor.execute("SELECT COUNT(*) FROM reunioes WHERE telefone_cliente IS NOT NULL AND telefone_cliente != ''")
        com_telefone = cursor.fetchone()[0]
        print_info(f"Reuniões com telefone: {com_telefone}")
        
        # Verifica tabela de respostas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_responses'")
        if not cursor.fetchone():
            print_error("Tabela 'client_responses' não existe!")
            conn.close()
            return False
        
        cursor.execute("SELECT COUNT(*) FROM client_responses")
        total_respostas = cursor.fetchone()[0]
        print_info(f"Respostas registradas: {total_respostas}")
        
        conn.close()
        
        if total_reunioes == 0:
            print_warning("Nenhuma reunião cadastrada! Crie uma reunião antes de testar.")
            return False
        
        if com_telefone == 0:
            print_warning("Nenhuma reunião tem telefone cadastrado!")
            return False
        
        print_success("Banco de dados OK!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao acessar banco: {e}")
        return False

def test_3_monitoring_status():
    """Teste 3: Monitoramento está ativo?"""
    print_header("TESTE 3: Status do Monitoramento")
    
    try:
        response = requests.get(f"{BASE_URL}/whatsapp/monitoring-status")
        
        if response.status_code == 200:
            data = response.json()
            
            is_monitoring = data.get('monitoring', False)
            monitored_count = data.get('monitored_phones', 0)
            phones_list = data.get('phones_list', [])
            
            if is_monitoring:
                print_success("Monitoramento está ATIVO")
            else:
                print_error("Monitoramento está INATIVO")
            
            print_info(f"Telefones monitorados: {monitored_count}")
            
            if phones_list:
                print_info("Lista de telefones:")
                for phone, meeting_id in phones_list[:5]:  # Mostra primeiros 5
                    print(f"   📱 {phone} → Reunião #{meeting_id}")
            else:
                print_warning("Nenhum telefone sendo monitorado!")
                print_info("Execute: POST /whatsapp/force-monitor-all")
            
            return is_monitoring and monitored_count > 0
        else:
            print_error(f"Falha ao verificar status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro: {e}")
        return False

def test_4_force_monitoring():
    """Teste 4: Força monitoramento de todas as reuniões"""
    print_header("TESTE 4: Forçando Monitoramento de Telefones")
    
    try:
        response = requests.post(f"{BASE_URL}/whatsapp/force-monitor-all")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                monitored = data.get('monitored_count', 0)
                total = data.get('total_monitored', 0)
                
                print_success(f"Monitoramento ativado com sucesso!")
                print_info(f"Telefones adicionados: {monitored}")
                print_info(f"Total monitorado: {total}")
                
                phones = data.get('phones', [])
                if phones:
                    print_info("Alguns telefones monitorados:")
                    for phone, meeting_id in phones[:3]:
                        print(f"   📱 {phone} → Reunião #{meeting_id}")
                
                return True
            else:
                print_error("Falha ao forçar monitoramento")
                return False
        else:
            print_error(f"Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro: {e}")
        return False

def test_5_webhook_simulation():
    """Teste 5: Simula webhook recebendo mensagem"""
    print_header("TESTE 5: Simulação de Webhook (Mensagem Real)")
    
    # Formatos diferentes para testar
    test_formats = [
        {
            "name": "Formato Evolution v2 Completo",
            "data": {
                "event": "messages.upsert",
                "instanceName": TEST_INSTANCE,
                "data": {
                    "key": {
                        "remoteJid": f"{YOUR_PHONE}@s.whatsapp.net",
                        "fromMe": False,
                        "id": "TEST123456"
                    },
                    "message": {
                        "conversation": "sim, confirmo minha presença"
                    },
                    "messageTimestamp": int(time.time())
                }
            }
        },
        {
            "name": "Formato Simplificado",
            "data": {
                "event": "messages.upsert",
                "instanceName": TEST_INSTANCE,
                "from": f"{YOUR_PHONE}@s.whatsapp.net",
                "body": "sim",
                "timestamp": int(time.time())
            }
        },
        {
            "name": "Formato Nested",
            "data": {
                "event": "message.upsert",
                "instanceName": TEST_INSTANCE,
                "data": {
                    "data": {
                        "from": YOUR_PHONE,
                        "body": "confirmo"
                    }
                }
            }
        }
    ]
    
    success_count = 0
    
    for test_format in test_formats:
        print(f"\n{Colors.CYAN}📤 Testando: {test_format['name']}{Colors.END}")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "apikey": API_KEY
            }
            
            response = requests.post(
                f"{BASE_URL}/webhook/evolution",
                json=test_format['data'],
                headers=headers,
                timeout=10
            )
            
            print_info(f"Status HTTP: {response.status_code}")
            
            try:
                result = response.json()
                print_info(f"Resposta: {json.dumps(result, indent=2)}")
                
                if result.get('status') == 'success' and result.get('processed'):
                    print_success(f"✅ {test_format['name']} - PROCESSADO COM SUCESSO!")
                    success_count += 1
                elif result.get('status') == 'ignored':
                    print_warning(f"Mensagem ignorada: {result.get('reason')}")
                else:
                    print_error(f"Mensagem não foi processada")
            except:
                print_warning(f"Resposta não é JSON: {response.text[:200]}")
            
            time.sleep(1)  # Aguarda 1 segundo entre testes
            
        except Exception as e:
            print_error(f"Erro ao testar formato: {e}")
    
    print(f"\n{Colors.BOLD}Resultado: {success_count}/{len(test_formats)} formatos processados com sucesso{Colors.END}")
    return success_count > 0

def test_6_check_responses_saved():
    """Teste 6: Verifica se respostas foram salvas no banco"""
    print_header("TESTE 6: Verificando Respostas Salvas")
    
    try:
        conn = sqlite3.connect('reunioes.db')
        cursor = conn.cursor()
        
        # Últimas 5 respostas
        cursor.execute('''
            SELECT cr.id, cr.meeting_id, cr.response_text, cr.status, cr.confidence, 
                   cr.received_at, r.titulo, r.convidado
            FROM client_responses cr
            LEFT JOIN reunioes r ON cr.meeting_id = r.id
            ORDER BY cr.received_at DESC
            LIMIT 5
        ''')
        
        responses = cursor.fetchall()
        
        if not responses:
            print_warning("Nenhuma resposta encontrada no banco!")
            print_info("Possíveis causas:")
            print("   1. Webhook não está sendo chamado pela Evolution API")
            print("   2. Telefone não está na lista de monitorados")
            print("   3. Formato da mensagem não está sendo reconhecido")
            conn.close()
            return False
        
        print_success(f"Encontradas {len(responses)} respostas recentes:")
        print()
        
        for resp in responses:
            resp_id, meeting_id, text, status, confidence, received_at, titulo, convidado = resp
            
            print(f"{Colors.BOLD}Resposta #{resp_id}{Colors.END}")
            print(f"   📅 Reunião: {titulo} ({convidado})")
            print(f"   💬 Texto: '{text}'")
            print(f"   📊 Status: {status}")
            print(f"   🎯 Confiança: {confidence:.2%}")
            print(f"   🕐 Recebido: {received_at}")
            print()
        
        conn.close()
        print_success("Respostas estão sendo salvas corretamente!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao verificar respostas: {e}")
        return False

def test_7_check_meeting_status_updated():
    """Teste 7: Verifica se status das reuniões foi atualizado"""
    print_header("TESTE 7: Verificando Atualização de Status")
    
    try:
        conn = sqlite3.connect('reunioes.db')
        cursor = conn.cursor()
        
        # Reuniões com status atualizado
        cursor.execute('''
            SELECT id, titulo, convidado, status_confirmacao, telefone_cliente
            FROM reunioes
            WHERE status_confirmacao != 'pending'
            ORDER BY id DESC
            LIMIT 5
        ''')
        
        meetings = cursor.fetchall()
        
        if not meetings:
            print_warning("Nenhuma reunião teve status atualizado!")
            print_info("Verifique:")
            print("   1. Se o threshold de confiança está muito alto")
            print("   2. Se a análise de resposta está funcionando")
            print("   3. Se o método _update_meeting_status_improved está sendo chamado")
            conn.close()
            return False
        
        print_success(f"Encontradas {len(meetings)} reuniões com status atualizado:")
        print()
        
        for meeting in meetings:
            meeting_id, titulo, convidado, status, telefone = meeting
            
            status_emoji = {
                'confirmed': '✅',
                'declined': '❌',
                'reschedule': '🔄',
                'pending': '⏳'
            }.get(status, '❓')
            
            print(f"{Colors.BOLD}Reunião #{meeting_id}{Colors.END}")
            print(f"   📋 Título: {titulo}")
            print(f"   👤 Convidado: {convidado}")
            print(f"   📱 Telefone: {telefone}")
            print(f"   {status_emoji} Status: {status.upper()}")
            print()
        
        conn.close()
        print_success("Status das reuniões está sendo atualizado!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao verificar status: {e}")
        return False

# ====================================
# MENU PRINCIPAL
# ====================================

def run_all_tests():
    """Executa todos os testes em sequência"""
    print_header("🧪 INICIANDO BATERIA COMPLETA DE TESTES")
    print_info(f"Servidor: {BASE_URL}")
    print_info(f"Telefone de teste: {YOUR_PHONE}")
    print_info(f"Instância: {TEST_INSTANCE}")
    print()
    
    results = {
        "1. Servidor Flask": test_1_server_health(),
        "2. Banco de Dados": test_2_database_check(),
        "3. Status Monitoramento": test_3_monitoring_status(),
        "4. Forçar Monitoramento": test_4_force_monitoring(),
        "5. Simulação Webhook": test_5_webhook_simulation(),
        "6. Respostas Salvas": test_6_check_responses_saved(),
        "7. Status Atualizado": test_7_check_meeting_status_updated()
    }
    
    # Relatório Final
    print_header("📊 RELATÓRIO FINAL")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASSOU{Colors.END}" if result else f"{Colors.RED}❌ FALHOU{Colors.END}"
        print(f"{test_name}: {status}")
    
    print()
    print(f"{Colors.BOLD}Resultado: {passed}/{total} testes passaram{Colors.END}")
    
    if passed == total:
        print_success("🎉 TODOS OS TESTES PASSARAM!")
    elif passed >= total * 0.7:
        print_warning(f"⚠️  Sistema parcialmente funcional ({passed}/{total})")
    else:
        print_error(f"❌ Sistema com problemas graves ({passed}/{total})")
    
    print()
    print_info("Próximos passos:")
    
    if not results["5. Simulação Webhook"]:
        print("   1. Verifique os logs do Flask durante o teste")
        print("   2. Confirme que o webhook está configurado na Evolution API")
        print("   3. Teste enviar uma mensagem REAL do WhatsApp")
    
    if not results["6. Respostas Salvas"]:
        print("   1. Verifique a função process_webhook_message()")
        print("   2. Confirme que _save_client_response_improved() está funcionando")
        print("   3. Teste com mensagens simples como 'sim' ou 'não'")
    
    if not results["7. Status Atualizado"]:
        print("   1. Verifique o threshold de confiança (linha ~1383)")
        print("   2. Teste a função ResponseAnalyzer.analyze_response()")
        print("   3. Confirme que _update_meeting_status_improved() não tem erros")

def interactive_menu():
    """Menu interativo para escolher testes"""
    while True:
        print_header("🧪 MENU DE TESTES DO WEBHOOK")
        print("1. ✅ Testar Servidor Flask")
        print("2. 💾 Testar Banco de Dados")
        print("3. 📡 Testar Status do Monitoramento")
        print("4. 🔄 Forçar Monitoramento de Telefones")
        print("5. 📤 Simular Webhook (Mensagem Teste)")
        print("6. 📋 Verificar Respostas Salvas")
        print("7. 📊 Verificar Status das Reuniões")
        print("8. 🚀 EXECUTAR TODOS OS TESTES")
        print("0. ❌ Sair")
        print()
        
        choice = input(f"{Colors.CYAN}Escolha uma opção: {Colors.END}").strip()
        
        if choice == "1":
            test_1_server_health()
        elif choice == "2":
            test_2_database_check()
        elif choice == "3":
            test_3_monitoring_status()
        elif choice == "4":
            test_4_force_monitoring()
        elif choice == "5":
            test_5_webhook_simulation()
        elif choice == "6":
            test_6_check_responses_saved()
        elif choice == "7":
            test_7_check_meeting_status_updated()
        elif choice == "8":
            run_all_tests()
        elif choice == "0":
            print_info("Encerrando testes...")
            break
        else:
            print_warning("Opção inválida!")
        
        input(f"\n{Colors.CYAN}Pressione ENTER para continuar...{Colors.END}")

# ====================================
# EXECUÇÃO PRINCIPAL
# ====================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Executa todos os testes automaticamente
        run_all_tests()
    else:
        # Menu interativo
        interactive_menu()