#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Relatórios Semanais - Agenda Executiva
Dispara relatórios automáticos das reuniões agendadas via WhatsApp
"""

import sqlite3
import schedule
import time
import threading
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Tuple
import requests
import re
from dataclasses import dataclass
from enum import Enum

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('relatorio_semanal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TipoRelatorio(Enum):
    """Tipos de relatórios disponíveis"""
    SEMANAL_COMPLETO = "semanal_completo"
    RESUMO_SEMANAL = "resumo_semanal"
    PROXIMOS_DIAS = "proximos_dias"
    CONFIRMACOES_PENDENTES = "confirmacoes_pendentes"

@dataclass
class ConfiguracaoRelatorio:
    """Configuração de um relatório específico"""
    id: str
    nome: str
    tipo: TipoRelatorio
    destinatarios: List[str]  # Lista de telefones
    horario_envio: str  # Formato HH:MM
    dias_semana: List[int]  # 0=segunda, 6=domingo
    ativo: bool
    template_personalizado: str = None

class EvolutionAPIReports:
    """Cliente para Evolution API focado em relatórios"""
    
    def __init__(self, config: Dict[str, str]):
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

    def normalize_phone_number(self, phone: str) -> str:
        """Normalização de telefone"""
        if not phone:
            return ""
        
        clean_phone = re.sub(r'\D', '', str(phone))
        
        if len(clean_phone) == 11 and clean_phone.startswith(('11', '21', '31', '41', '51', '61', '71', '81', '91')):
            return '55' + clean_phone
        elif len(clean_phone) == 13 and clean_phone.startswith('55'):
            return clean_phone
        elif len(clean_phone) == 10 and clean_phone.startswith(('11', '21', '31', '41', '51', '61', '71', '81', '91')):
            ddd = clean_phone[:2]
            numero = clean_phone[2:]
            return f"55{ddd}9{numero}"
        else:
            logger.warning(f"Formato não reconhecido: {clean_phone}")
            return clean_phone

    def send_message(self, phone: str, message: str) -> Tuple[bool, str]:
        """Envia mensagem via Evolution API"""
        try:
            normalized_phone = self.normalize_phone_number(phone)
            logger.info(f"📤 Enviando relatório para {normalized_phone}")
            
            payload = {
                "number": normalized_phone,
                "textMessage": {
                    "text": message
                }
            }
            
            endpoint = f'/message/sendText/{self.instance_name}'
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Relatório enviado com sucesso para {normalized_phone}")
                return True, "Relatório enviado com sucesso"
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Falha no envio: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Erro interno no envio: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return False, error_msg

class RelatorioDados:
    """Classe para buscar dados das reuniões"""
    
    def __init__(self, database_path: str = 'reunioes.db'):
        self.database_path = database_path

    def get_reunioes_periodo(self, data_inicio: date, data_fim: date) -> List[Dict]:
        """Busca reuniões em um período específico"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, titulo, convidado, data_hora, assunto, link, 
                           nome_cliente, telefone_cliente, local_reuniao, status_confirmacao
                    FROM reunioes 
                    WHERE DATE(data_hora) BETWEEN ? AND ?
                    ORDER BY data_hora
                ''', (data_inicio.isoformat(), data_fim.isoformat()))
                
                reunioes = []
                for row in cursor.fetchall():
                    reunioes.append({
                        'id': row[0],
                        'titulo': row[1],
                        'convidado': row[2],
                        'data_hora': datetime.fromisoformat(row[3]) if row[3] else None,
                        'assunto': row[4],
                        'link': row[5] or '',
                        'nome_cliente': row[6] or '',
                        'telefone_cliente': row[7] or '',
                        'local_reuniao': row[8] or '',
                        'status_confirmacao': row[9] or 'pending'
                    })
                
                return reunioes
                
        except Exception as e:
            logger.error(f"Erro ao buscar reuniões: {e}")
            return []

    def get_semana_atual(self) -> Tuple[date, date]:
        """Retorna primeiro e último dia da semana atual (segunda a domingo)"""
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def get_proxima_semana(self) -> Tuple[date, date]:
        """Retorna primeiro e último dia da próxima semana"""
        monday, sunday = self.get_semana_atual()
        next_monday = monday + timedelta(days=7)
        next_sunday = sunday + timedelta(days=7)
        return next_monday, next_sunday

    def get_estatisticas_semana(self, reunioes: List[Dict]) -> Dict:
        """Calcula estatísticas da semana"""
        stats = {
            'total': len(reunioes),
            'confirmadas': len([r for r in reunioes if r['status_confirmacao'] == 'confirmed']),
            'pendentes': len([r for r in reunioes if r['status_confirmacao'] == 'pending']),
            'declinadas': len([r for r in reunioes if r['status_confirmacao'] == 'declined']),
            'com_link': len([r for r in reunioes if r['link']]),
            'presencial': len([r for r in reunioes if r['local_reuniao'] and not r['link']]),
            'clientes_unicos': len(set([r['nome_cliente'] for r in reunioes if r['nome_cliente']]))
        }
        return stats

class TemplateManager:
    """Gerenciador de templates para relatórios"""
    
    @staticmethod
    def get_template_semanal_completo() -> str:
        """Template completo para relatório semanal"""
        return """📅 **RELATÓRIO SEMANAL DE REUNIÕES**
Período: {data_inicio} a {data_fim}

📊 **RESUMO EXECUTIVO**
• Total de reuniões: {total_reunioes}
• Confirmadas: {confirmadas} ✅
• Pendentes: {pendentes} ⏳
• Declinadas: {declinadas} ❌
• Clientes únicos: {clientes_unicos}

🏢 **MODALIDADES**
• Online (com link): {com_link}
• Presencial: {presencial}

📋 **AGENDA DETALHADA**
{agenda_detalhada}

📈 **STATUS DE CONFIRMAÇÕES**
{status_confirmacoes}

---
**Relatório automático - Agenda Executiva** 🤖
Gerado em: {data_geracao}"""

    @staticmethod
    def get_template_resumo_semanal() -> str:
        """Template resumido para relatório semanal"""
        return """📅 **RESUMO DA SEMANA**
{data_inicio} a {data_fim}

📊 {total_reunioes} reuniões • {confirmadas} confirmadas • {pendentes} pendentes

🗓️ **PRÓXIMAS REUNIÕES**
{proximas_reunioes}

⚠️ **CONFIRMAÇÕES PENDENTES**
{confirmacoes_pendentes}

---
Relatório automático 🤖 {data_geracao}"""

    @staticmethod
    def get_template_confirmacoes_pendentes() -> str:
        """Template para confirmações pendentes"""
        return """⏳ **CONFIRMAÇÕES PENDENTES**

{total_pendentes} reuniões aguardando confirmação:

{lista_pendentes}

💡 **Ação necessária:** Entre em contato para confirmar presença

---
Relatório de pendências • {data_geracao}"""

    @staticmethod
    def format_reuniao_detalhada(self, reuniao: Dict) -> str:
        """Formata reunião para exibição detalhada"""
        data_formatada = reuniao['data_hora'].strftime('%d/%m %H:%M')
        
        # Emoji baseado no status
        status_emoji = {
            'confirmed': '✅',
            'pending': '⏳', 
            'declined': '❌'
        }.get(reuniao['status_confirmacao'], '❔')
        
        # Modalidade
        modalidade = '🔗 Online' if reuniao['link'] else f"🏢 {reuniao['local_reuniao']}" if reuniao['local_reuniao'] else '📍 A definir'
        
        return f"""
{status_emoji} **{reuniao['titulo']}**
   📅 {data_formatada} | {modalidade}
   👤 {reuniao['convidado']} ({reuniao['nome_cliente'] or 'Cliente não informado'})
   📝 {reuniao['assunto'][:50]}{'...' if len(reuniao['assunto']) > 50 else ''}
"""

    @staticmethod
    def format_reuniao_resumida(reuniao: Dict) -> str:
        """Formata reunião para exibição resumida"""
        data_formatada = reuniao['data_hora'].strftime('%d/%m %H:%M')
        status_emoji = {'confirmed': '✅', 'pending': '⏳', 'declined': '❌'}.get(reuniao['status_confirmacao'], '❔')
        
        return f"{status_emoji} {data_formatada} - {reuniao['titulo']} com {reuniao['convidado']}"

class GeradorRelatorios:
    """Classe principal para gerar relatórios"""
    
    def __init__(self, evolution_api: EvolutionAPIReports, relatorio_dados: RelatorioDados):
        self.evolution_api = evolution_api
        self.relatorio_dados = relatorio_dados
        self.template_manager = TemplateManager()

    def gerar_relatorio_semanal_completo(self, data_inicio: date = None, data_fim: date = None) -> str:
        """Gera relatório semanal completo"""
        try:
            if not data_inicio or not data_fim:
                data_inicio, data_fim = self.relatorio_dados.get_semana_atual()
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            stats = self.relatorio_dados.get_estatisticas_semana(reunioes)
            
            # Agenda detalhada
            agenda_detalhada = ""
            for reuniao in reunioes:
                agenda_detalhada += self.template_manager.format_reuniao_detalhada(reuniao)
            
            if not agenda_detalhada:
                agenda_detalhada = "📭 Nenhuma reunião agendada para este período"
            
            # Status de confirmações
            confirmacoes_pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            status_confirmacoes = ""
            
            if confirmacoes_pendentes:
                status_confirmacoes = "⚠️ **PENDENTES DE CONFIRMAÇÃO:**\n"
                for reuniao in confirmacoes_pendentes:
                    status_confirmacoes += f"• {reuniao['data_hora'].strftime('%d/%m %H:%M')} - {reuniao['titulo']} ({reuniao['convidado']})\n"
            else:
                status_confirmacoes = "✅ Todas as reuniões confirmadas ou processadas"
            
            # Monta relatório
            template = self.template_manager.get_template_semanal_completo()
            relatorio = template.format(
                data_inicio=data_inicio.strftime('%d/%m/%Y'),
                data_fim=data_fim.strftime('%d/%m/%Y'),
                total_reunioes=stats['total'],
                confirmadas=stats['confirmadas'],
                pendentes=stats['pendentes'],
                declinadas=stats['declinadas'],
                clientes_unicos=stats['clientes_unicos'],
                com_link=stats['com_link'],
                presencial=stats['presencial'],
                agenda_detalhada=agenda_detalhada,
                status_confirmacoes=status_confirmacoes,
                data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório semanal completo: {e}")
            return f"❌ Erro ao gerar relatório: {str(e)}"

    def gerar_resumo_semanal(self, data_inicio: date = None, data_fim: date = None) -> str:
        """Gera resumo semanal"""
        try:
            if not data_inicio or not data_fim:
                data_inicio, data_fim = self.relatorio_dados.get_semana_atual()
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            stats = self.relatorio_dados.get_estatisticas_semana(reunioes)
            
            # Próximas 3 reuniões
            reunioes_futuras = [r for r in reunioes if r['data_hora'] >= datetime.now()][:3]
            proximas_reunioes = ""
            for reuniao in reunioes_futuras:
                proximas_reunioes += f"• {self.template_manager.format_reuniao_resumida(reuniao)}\n"
            
            if not proximas_reunioes:
                proximas_reunioes = "📭 Nenhuma reunião próxima"
            
            # Confirmações pendentes
            pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            confirmacoes_pendentes = ""
            for reuniao in pendentes[:3]:  # Máximo 3
                confirmacoes_pendentes += f"• {self.template_manager.format_reuniao_resumida(reuniao)}\n"
                
            if not confirmacoes_pendentes:
                confirmacoes_pendentes = "✅ Nenhuma pendência"
            
            template = self.template_manager.get_template_resumo_semanal()
            relatorio = template.format(
                data_inicio=data_inicio.strftime('%d/%m'),
                data_fim=data_fim.strftime('%d/%m'),
                total_reunioes=stats['total'],
                confirmadas=stats['confirmadas'],
                pendentes=stats['pendentes'],
                proximas_reunioes=proximas_reunioes,
                confirmacoes_pendentes=confirmacoes_pendentes,
                data_geracao=datetime.now().strftime('%d/%m %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo semanal: {e}")
            return f"❌ Erro ao gerar resumo: {str(e)}"

    def gerar_relatorio_confirmacoes_pendentes(self) -> str:
        """Gera relatório de confirmações pendentes"""
        try:
            # Próximos 15 dias
            data_inicio = date.today()
            data_fim = data_inicio + timedelta(days=15)
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            
            if not pendentes:
                return "✅ **CONFIRMAÇÕES EM DIA**\n\nNenhuma reunião pendente de confirmação nos próximos 15 dias.\n\n---\nRelatório de pendências • " + datetime.now().strftime('%d/%m/%Y %H:%M')
            
            lista_pendentes = ""
            for reuniao in pendentes:
                dias_restantes = (reuniao['data_hora'].date() - date.today()).days
                urgencia = "🔴" if dias_restantes <= 1 else "🟡" if dias_restantes <= 3 else "🟢"
                
                lista_pendentes += f"""
{urgencia} **{reuniao['titulo']}**
   📅 {reuniao['data_hora'].strftime('%d/%m/%Y %H:%M')} ({dias_restantes} dias)
   👤 {reuniao['convidado']} ({reuniao['nome_cliente'] or 'Cliente não informado'})
   📞 {reuniao['telefone_cliente'] or 'Telefone não informado'}
"""
            
            template = self.template_manager.get_template_confirmacoes_pendentes()
            relatorio = template.format(
                total_pendentes=len(pendentes),
                lista_pendentes=lista_pendentes,
                data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de pendências: {e}")
            return f"❌ Erro ao gerar relatório de pendências: {str(e)}"

    def enviar_relatorio(self, tipo_relatorio: TipoRelatorio, destinatarios: List[str], 
                        data_inicio: date = None, data_fim: date = None) -> Dict[str, Any]:
        """Envia relatório para destinatários"""
        try:
            logger.info(f"📊 Gerando relatório: {tipo_relatorio.value}")
            
            # Gera relatório baseado no tipo
            if tipo_relatorio == TipoRelatorio.SEMANAL_COMPLETO:
                relatorio = self.gerar_relatorio_semanal_completo(data_inicio, data_fim)
            elif tipo_relatorio == TipoRelatorio.RESUMO_SEMANAL:
                relatorio = self.gerar_resumo_semanal(data_inicio, data_fim)
            elif tipo_relatorio == TipoRelatorio.CONFIRMACOES_PENDENTES:
                relatorio = self.gerar_relatorio_confirmacoes_pendentes()
            else:
                raise ValueError(f"Tipo de relatório não implementado: {tipo_relatorio}")
            
            # Envia para cada destinatário
            resultados = {
                'success': True,
                'enviados': 0,
                'falhas': 0,
                'detalhes': [],
                'relatorio_gerado': relatorio[:200] + '...' if len(relatorio) > 200 else relatorio
            }
            
            for telefone in destinatarios:
                try:
                    success, message = self.evolution_api.send_message(telefone, relatorio)
                    
                    if success:
                        resultados['enviados'] += 1
                        resultados['detalhes'].append(f"✅ {telefone}: Enviado")
                        logger.info(f"✅ Relatório enviado para {telefone}")
                    else:
                        resultados['falhas'] += 1
                        resultados['detalhes'].append(f"❌ {telefone}: {message}")
                        logger.error(f"❌ Falha para {telefone}: {message}")
                        
                    # Delay entre envios
                    time.sleep(2)
                    
                except Exception as e:
                    resultados['falhas'] += 1
                    resultados['detalhes'].append(f"💥 {telefone}: Erro interno - {str(e)}")
                    logger.error(f"💥 Erro interno para {telefone}: {e}")
            
            # Status geral
            if resultados['falhas'] > 0:
                resultados['success'] = False
                
            logger.info(f"📊 Relatório finalizado: {resultados['enviados']} enviados, {resultados['falhas']} falhas")
            
            return resultados
            
        except Exception as e:
            logger.error(f"💥 Erro crítico no envio de relatório: {e}")
            return {
                'success': False,
                'enviados': 0,
                'falhas': len(destinatarios),
                'error': str(e),
                'detalhes': [f"💥 Erro crítico: {str(e)}"]
            }

class ConfiguradorRelatorios:
    """Gerencia configurações de relatórios automáticos"""
    
    def __init__(self, database_path: str = 'relatorios_config.db'):
        self.database_path = database_path
        self.init_db()

    def init_db(self):
        """Inicializa banco de configurações"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS configuracoes_relatorios (
                        id TEXT PRIMARY KEY,
                        nome TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        destinatarios TEXT NOT NULL,
                        horario_envio TEXT NOT NULL,
                        dias_semana TEXT NOT NULL,
                        ativo BOOLEAN DEFAULT 1,
                        template_personalizado TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs_relatorios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        configuracao_id TEXT,
                        data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                        tipo_relatorio TEXT,
                        destinatarios_alvo TEXT,
                        enviados INTEGER,
                        falhas INTEGER,
                        status TEXT,
                        detalhes TEXT,
                        FOREIGN KEY (configuracao_id) REFERENCES configuracoes_relatorios (id)
                    )
                ''')
                
                conn.commit()
                
                # Insere configurações padrão se não existirem
                self._criar_configuracoes_padrao()
                
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de configurações: {e}")

    def _criar_configuracoes_padrao(self):
        """Cria configurações padrão"""
        try:
            configuracoes_padrao = [
                {
                    'id': 'resumo_segunda',
                    'nome': 'Resumo Segunda-feira',
                    'tipo': 'resumo_semanal',
                    'destinatarios': ['21982161008'],  # SEU NÚMERO
                    'horario_envio': '09:00',
                    'dias_semana': [0],  # Segunda-feira
                    'ativo': True
                },
                {
                    'id': 'completo_sexta',
                    'nome': 'Relatório Completo Sexta-feira', 
                    'tipo': 'semanal_completo',
                    'destinatarios': ['21982161008'],  # SEU NÚMERO
                    'horario_envio': '17:30',
                    'dias_semana': [4],  # Sexta-feira
                    'ativo': False
                },
                {
                    'id': 'pendencias_diario',
                    'nome': 'Pendências Diárias',
                    'tipo': 'confirmacoes_pendentes',
                    'destinatarios': ['21982161008'],  # SEU NÚMERO
                    'horario_envio': '08:30',
                    'dias_semana': [0, 1, 2, 3, 4],  # Segunda a sexta
                    'ativo': False
                }
            ]
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for config in configuracoes_padrao:
                    cursor.execute('''
                        INSERT OR IGNORE INTO configuracoes_relatorios 
                        (id, nome, tipo, destinatarios, horario_envio, dias_semana, ativo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        config['id'],
                        config['nome'], 
                        config['tipo'],
                        json.dumps(config['destinatarios']),
                        config['horario_envio'],
                        json.dumps(config['dias_semana']),
                        config['ativo']
                    ))
                
                conn.commit()
                logger.info("✅ Configurações padrão criadas")
                
        except Exception as e:
            logger.error(f"Erro ao criar configurações padrão: {e}")

    def obter_configuracoes_ativas(self) -> List[ConfiguracaoRelatorio]:
        """Obtém todas as configurações ativas"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, nome, tipo, destinatarios, horario_envio, dias_semana, ativo, template_personalizado
                    FROM configuracoes_relatorios 
                    WHERE ativo = 1
                ''')
                
                configuracoes = []
                for row in cursor.fetchall():
                    config = ConfiguracaoRelatorio(
                        id=row[0],
                        nome=row[1],
                        tipo=TipoRelatorio(row[2]),
                        destinatarios=json.loads(row[3]),
                        horario_envio=row[4],
                        dias_semana=json.loads(row[5]),
                        ativo=bool(row[6]),
                        template_personalizado=row[7]
                    )
                    configuracoes.append(config)
                
                return configuracoes
                
        except Exception as e:
            logger.error(f"Erro ao obter configurações: {e}")
            return []

    def salvar_configuracao(self, config: ConfiguracaoRelatorio) -> bool:
        """Salva ou atualiza uma configuração"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO configuracoes_relatorios 
                    (id, nome, tipo, destinatarios, horario_envio, dias_semana, ativo, template_personalizado, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    config.id,
                    config.nome,
                    config.tipo.value,
                    json.dumps(config.destinatarios),
                    config.horario_envio,
                    json.dumps(config.dias_semana),
                    config.ativo,
                    config.template_personalizado
                ))
                
                conn.commit()
                logger.info(f"✅ Configuração salva: {config.id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return False

    def log_envio_relatorio(self, config_id: str, resultados: Dict[str, Any]):
        """Registra log de envio de relatório"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO logs_relatorios 
                    (configuracao_id, destinatarios_alvo, enviados, falhas, status, detalhes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    config_id,
                    len(resultados.get('detalhes', [])),
                    resultados.get('enviados', 0),
                    resultados.get('falhas', 0),
                    'success' if resultados.get('success') else 'failed',
                    json.dumps(resultados.get('detalhes', []))
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

class SchedulerRelatorios:
    """Scheduler para execução automática dos relatórios"""
    
    def __init__(self, gerador_relatorios: GeradorRelatorios, configurador: ConfiguradorRelatorios):
        self.gerador_relatorios = gerador_relatorios
        self.configurador = configurador
        self.running = False

    def agendar_relatorios(self):
        """Agenda todos os relatórios configurados"""
        try:
            configuracoes = self.configurador.obter_configuracoes_ativas()
            
            # Limpa agendamentos anteriores
            schedule.clear()
            
            for config in configuracoes:
                self._agendar_configuracao(config)
            
            logger.info(f"📅 {len(configuracoes)} relatórios agendados")
            
        except Exception as e:
            logger.error(f"Erro ao agendar relatórios: {e}")

    def _agendar_configuracao(self, config: ConfiguracaoRelatorio):
        """Agenda uma configuração específica"""
        try:
            def job_wrapper():
                self._executar_relatorio(config)
            
            # Agenda para cada dia da semana especificado
            for dia_semana in config.dias_semana:
                dia_nome = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][dia_semana]
                
                # Usa o método correto do schedule
                scheduler_job = getattr(schedule.every(), dia_nome)
                scheduler_job.at(config.horario_envio).do(job_wrapper)
                
                logger.info(f"📅 Agendado: {config.nome} - {dia_nome} às {config.horario_envio}")
                
        except Exception as e:
            logger.error(f"Erro ao agendar configuração {config.id}: {e}")

    def _executar_relatorio(self, config: ConfiguracaoRelatorio):
        """Executa um relatório específico"""
        try:
            logger.info(f"🚀 Executando relatório: {config.nome}")
            
            # Determina período baseado no tipo
            if config.tipo in [TipoRelatorio.SEMANAL_COMPLETO, TipoRelatorio.RESUMO_SEMANAL]:
                # Para relatórios semanais, usa semana atual
                data_inicio, data_fim = self.gerador_relatorios.relatorio_dados.get_semana_atual()
                resultados = self.gerador_relatorios.enviar_relatorio(
                    config.tipo, config.destinatarios, data_inicio, data_fim
                )
            else:
                # Para outros tipos, não precisa de período específico
                resultados = self.gerador_relatorios.enviar_relatorio(
                    config.tipo, config.destinatarios
                )
            
            # Log do resultado
            self.configurador.log_envio_relatorio(config.id, resultados)
            
            if resultados['success']:
                logger.info(f"✅ Relatório {config.nome} executado com sucesso")
            else:
                logger.error(f"❌ Falha no relatório {config.nome}: {resultados}")
                
        except Exception as e:
            logger.error(f"💥 Erro ao executar relatório {config.nome}: {e}")
            # Log do erro
            error_result = {
                'success': False,
                'enviados': 0,
                'falhas': len(config.destinatarios),
                'detalhes': [f"Erro interno: {str(e)}"]
            }
            self.configurador.log_envio_relatorio(config.id, error_result)

    def iniciar_scheduler(self):
        """Inicia o scheduler em loop contínuo"""
        self.running = True
        logger.info("🚀 Scheduler de relatórios iniciado")
        
        try:
            while self.running:
                # Reagenda relatórios a cada hora para pegar mudanças
                current_time = datetime.now()
                if current_time.minute == 0:  # A cada hora cheia
                    self.agendar_relatorios()
                
                # Executa tarefas pendentes
                schedule.run_pending()
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler interrompido pelo usuário")
        except Exception as e:
            logger.error(f"💥 Erro no scheduler: {e}")
        finally:
            self.running = False

    def parar_scheduler(self):
        """Para o scheduler"""
        self.running = False
        logger.info("🛑 Scheduler de relatórios parado")

# CORREÇÃO DOS MÉTODOS ESTÁTICOS NO TEMPLATE MANAGER
class TemplateManager:
    """Gerenciador de templates para relatórios - VERSÃO CORRIGIDA"""
    
    @staticmethod
    def get_template_semanal_completo() -> str:
        """Template completo para relatório semanal"""
        return """📅 **RELATÓRIO SEMANAL DE REUNIÕES**
Período: {data_inicio} a {data_fim}

📊 **RESUMO EXECUTIVO**
• Total de reuniões: {total_reunioes}
• Confirmadas: {confirmadas} ✅
• Pendentes: {pendentes} ⏳
• Declinadas: {declinadas} ❌
• Clientes únicos: {clientes_unicos}

🏢 **MODALIDADES**
• Online (com link): {com_link}
• Presencial: {presencial}

📋 **AGENDA DETALHADA**
{agenda_detalhada}

📈 **STATUS DE CONFIRMAÇÕES**
{status_confirmacoes}

---
**Relatório automático - Agenda Executiva** 🤖
Gerado em: {data_geracao}"""

    @staticmethod
    def get_template_resumo_semanal() -> str:
        """Template resumido para relatório semanal"""
        return """📅 **RESUMO DA SEMANA**
{data_inicio} a {data_fim}

📊 {total_reunioes} reuniões • {confirmadas} confirmadas • {pendentes} pendentes

🗓️ **PRÓXIMAS REUNIÕES**
{proximas_reunioes}

⚠️ **CONFIRMAÇÕES PENDENTES**
{confirmacoes_pendentes}

---
Relatório automático 🤖 {data_geracao}"""

    @staticmethod
    def get_template_confirmacoes_pendentes() -> str:
        """Template para confirmações pendentes"""
        return """⏳ **CONFIRMAÇÕES PENDENTES**

{total_pendentes} reuniões aguardando confirmação:

{lista_pendentes}

💡 **Ação necessária:** Entre em contato para confirmar presença

---
Relatório de pendências • {data_geracao}"""

    @staticmethod
    def format_reuniao_detalhada(reuniao: Dict) -> str:
        """CORREÇÃO: Removido 'self' do método estático"""
        data_formatada = reuniao['data_hora'].strftime('%d/%m %H:%M')
        
        # Emoji baseado no status
        status_emoji = {
            'confirmed': '✅',
            'pending': '⏳', 
            'declined': '❌'
        }.get(reuniao['status_confirmacao'], '❔')
        
        # Modalidade
        modalidade = '🔗 Online' if reuniao['link'] else f"🏢 {reuniao['local_reuniao']}" if reuniao['local_reuniao'] else '📍 A definir'
        
        return f"""
{status_emoji} **{reuniao['titulo']}**
   📅 {data_formatada} | {modalidade}
   👤 {reuniao['convidado']} ({reuniao['nome_cliente'] or 'Cliente não informado'})
   📝 {reuniao['assunto'][:50]}{'...' if len(reuniao['assunto']) > 50 else ''}
"""

    @staticmethod
    def format_reuniao_resumida(reuniao: Dict) -> str:
        """Formata reunião para exibição resumida"""
        data_formatada = reuniao['data_hora'].strftime('%d/%m %H:%M')
        status_emoji = {'confirmed': '✅', 'pending': '⏳', 'declined': '❌'}.get(reuniao['status_confirmacao'], '❔')
        
        return f"{status_emoji} {data_formatada} - {reuniao['titulo']} com {reuniao['convidado']}"

# CORREÇÃO NA CLASSE GERADORRELATORIOS
class GeradorRelatorios:
    """Classe principal para gerar relatórios - VERSÃO CORRIGIDA"""
    
    def __init__(self, evolution_api: EvolutionAPIReports, relatorio_dados: RelatorioDados):
        self.evolution_api = evolution_api
        self.relatorio_dados = relatorio_dados
        self.template_manager = TemplateManager()

    def gerar_relatorio_semanal_completo(self, data_inicio: date = None, data_fim: date = None) -> str:
        """Gera relatório semanal completo - CORRIGIDO"""
        try:
            if not data_inicio or not data_fim:
                data_inicio, data_fim = self.relatorio_dados.get_semana_atual()
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            stats = self.relatorio_dados.get_estatisticas_semana(reunioes)
            
            # Agenda detalhada - CORREÇÃO: chamada correta do método estático
            agenda_detalhada = ""
            for reuniao in reunioes:
                agenda_detalhada += TemplateManager.format_reuniao_detalhada(reuniao)
            
            if not agenda_detalhada:
                agenda_detalhada = "📭 Nenhuma reunião agendada para este período"
            
            # Status de confirmações
            confirmacoes_pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            status_confirmacoes = ""
            
            if confirmacoes_pendentes:
                status_confirmacoes = "⚠️ **PENDENTES DE CONFIRMAÇÃO:**\n"
                for reuniao in confirmacoes_pendentes:
                    status_confirmacoes += f"• {reuniao['data_hora'].strftime('%d/%m %H:%M')} - {reuniao['titulo']} ({reuniao['convidado']})\n"
            else:
                status_confirmacoes = "✅ Todas as reuniões confirmadas ou processadas"
            
            # Monta relatório
            template = TemplateManager.get_template_semanal_completo()
            relatorio = template.format(
                data_inicio=data_inicio.strftime('%d/%m/%Y'),
                data_fim=data_fim.strftime('%d/%m/%Y'),
                total_reunioes=stats['total'],
                confirmadas=stats['confirmadas'],
                pendentes=stats['pendentes'],
                declinadas=stats['declinadas'],
                clientes_unicos=stats['clientes_unicos'],
                com_link=stats['com_link'],
                presencial=stats['presencial'],
                agenda_detalhada=agenda_detalhada,
                status_confirmacoes=status_confirmacoes,
                data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório semanal completo: {e}")
            return f"❌ Erro ao gerar relatório: {str(e)}"

    def gerar_resumo_semanal(self, data_inicio: date = None, data_fim: date = None) -> str:
        """Gera resumo semanal - CORRIGIDO"""
        try:
            if not data_inicio or not data_fim:
                data_inicio, data_fim = self.relatorio_dados.get_semana_atual()
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            stats = self.relatorio_dados.get_estatisticas_semana(reunioes)
            
            # Próximas 3 reuniões - CORREÇÃO: chamada correta do método estático
            reunioes_futuras = [r for r in reunioes if r['data_hora'] >= datetime.now()][:3]
            proximas_reunioes = ""
            for reuniao in reunioes_futuras:
                proximas_reunioes += f"• {TemplateManager.format_reuniao_resumida(reuniao)}\n"
            
            if not proximas_reunioes:
                proximas_reunioes = "📭 Nenhuma reunião próxima"
            
            # Confirmações pendentes - CORREÇÃO: chamada correta do método estático
            pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            confirmacoes_pendentes = ""
            for reuniao in pendentes[:3]:  # Máximo 3
                confirmacoes_pendentes += f"• {TemplateManager.format_reuniao_resumida(reuniao)}\n"
                
            if not confirmacoes_pendentes:
                confirmacoes_pendentes = "✅ Nenhuma pendência"
            
            template = TemplateManager.get_template_resumo_semanal()
            relatorio = template.format(
                data_inicio=data_inicio.strftime('%d/%m'),
                data_fim=data_fim.strftime('%d/%m'),
                total_reunioes=stats['total'],
                confirmadas=stats['confirmadas'],
                pendentes=stats['pendentes'],
                proximas_reunioes=proximas_reunioes,
                confirmacoes_pendentes=confirmacoes_pendentes,
                data_geracao=datetime.now().strftime('%d/%m %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo semanal: {e}")
            return f"❌ Erro ao gerar resumo: {str(e)}"

    def gerar_relatorio_confirmacoes_pendentes(self) -> str:
        """Gera relatório de confirmações pendentes"""
        try:
            # Próximos 15 dias
            data_inicio = date.today()
            data_fim = data_inicio + timedelta(days=15)
            
            reunioes = self.relatorio_dados.get_reunioes_periodo(data_inicio, data_fim)
            pendentes = [r for r in reunioes if r['status_confirmacao'] == 'pending']
            
            if not pendentes:
                return "✅ **CONFIRMAÇÕES EM DIA**\n\nNenhuma reunião pendente de confirmação nos próximos 15 dias.\n\n---\nRelatório de pendências • " + datetime.now().strftime('%d/%m/%Y %H:%M')
            
            lista_pendentes = ""
            for reuniao in pendentes:
                dias_restantes = (reuniao['data_hora'].date() - date.today()).days
                urgencia = "🔴" if dias_restantes <= 1 else "🟡" if dias_restantes <= 3 else "🟢"
                
                lista_pendentes += f"""
{urgencia} **{reuniao['titulo']}**
   📅 {reuniao['data_hora'].strftime('%d/%m/%Y %H:%M')} ({dias_restantes} dias)
   👤 {reuniao['convidado']} ({reuniao['nome_cliente'] or 'Cliente não informado'})
   📞 {reuniao['telefone_cliente'] or 'Telefone não informado'}
"""
            
            template = TemplateManager.get_template_confirmacoes_pendentes()
            relatorio = template.format(
                total_pendentes=len(pendentes),
                lista_pendentes=lista_pendentes,
                data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M')
            )
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de pendências: {e}")
            return f"❌ Erro ao gerar relatório de pendências: {str(e)}"

    def enviar_relatorio(self, tipo_relatorio: TipoRelatorio, destinatarios: List[str], 
                        data_inicio: date = None, data_fim: date = None) -> Dict[str, Any]:
        """Envia relatório para destinatários"""
        try:
            logger.info(f"📊 Gerando relatório: {tipo_relatorio.value}")
            
            # Gera relatório baseado no tipo
            if tipo_relatorio == TipoRelatorio.SEMANAL_COMPLETO:
                relatorio = self.gerar_relatorio_semanal_completo(data_inicio, data_fim)
            elif tipo_relatorio == TipoRelatorio.RESUMO_SEMANAL:
                relatorio = self.gerar_resumo_semanal(data_inicio, data_fim)
            elif tipo_relatorio == TipoRelatorio.CONFIRMACOES_PENDENTES:
                relatorio = self.gerar_relatorio_confirmacoes_pendentes()
            else:
                raise ValueError(f"Tipo de relatório não implementado: {tipo_relatorio}")
            
            # Envia para cada destinatário
            resultados = {
                'success': True,
                'enviados': 0,
                'falhas': 0,
                'detalhes': [],
                'relatorio_gerado': relatorio[:200] + '...' if len(relatorio) > 200 else relatorio
            }
            
            for telefone in destinatarios:
                try:
                    success, message = self.evolution_api.send_message(telefone, relatorio)
                    
                    if success:
                        resultados['enviados'] += 1
                        resultados['detalhes'].append(f"✅ {telefone}: Enviado")
                        logger.info(f"✅ Relatório enviado para {telefone}")
                    else:
                        resultados['falhas'] += 1
                        resultados['detalhes'].append(f"❌ {telefone}: {message}")
                        logger.error(f"❌ Falha para {telefone}: {message}")
                        
                    # Delay entre envios
                    time.sleep(2)
                    
                except Exception as e:
                    resultados['falhas'] += 1
                    resultados['detalhes'].append(f"💥 {telefone}: Erro interno - {str(e)}")
                    logger.error(f"💥 Erro interno para {telefone}: {e}")
            
            # Status geral
            if resultados['falhas'] > 0:
                resultados['success'] = False
                
            logger.info(f"📊 Relatório finalizado: {resultados['enviados']} enviados, {resultados['falhas']} falhas")
            
            return resultados
            
        except Exception as e:
            logger.error(f"💥 Erro crítico no envio de relatório: {e}")
            return {
                'success': False,
                'enviados': 0,
                'falhas': len(destinatarios),
                'error': str(e),
                'detalhes': [f"💥 Erro crítico: {str(e)}"]
            }

def main():
    """Função principal do sistema de relatórios"""
    print("🚀 Iniciando Sistema de Relatórios Semanais...")
    
    try:
        # Configuração da Evolution API (mesma do app.py principal)
        EVOLUTION_CONFIG = {
            'base_url': 'http://82.25.69.24:8090',
            'api_key': 'olvjg1k1ldmbhyl8owi6',
            'instance_name': 'marco_reunioes_bot'
        }
        
        # Inicializa componentes
        evolution_api = EvolutionAPIReports(EVOLUTION_CONFIG)
        relatorio_dados = RelatorioDados('reunioes.db')  # Mesmo banco do app principal
        gerador = GeradorRelatorios(evolution_api, relatorio_dados)
        configurador = ConfiguradorRelatorios()
        scheduler = SchedulerRelatorios(gerador, configurador)
        
        print("✅ Componentes inicializados")
        
        # Testa relatório
        print("\n📊 Gerando relatório de teste...")
        relatorio_teste = gerador.gerar_resumo_semanal()
        print("Preview do relatório:")
        print("-" * 50)
        print(relatorio_teste[:300] + "...")
        print("-" * 50)
        
        # Inicia scheduler
        print("\n⏰ Iniciando scheduler automático...")
        scheduler.agendar_relatorios()
        
        print("📅 Relatórios agendados! Pressione Ctrl+C para parar.")
        scheduler.iniciar_scheduler()
        
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        logger.error(f"Erro crítico na inicialização: {e}")

def testar_relatorio_manual():
    """Função para testar geração manual de relatórios"""
    print("🧪 Teste Manual de Relatórios")
    
    try:
        EVOLUTION_CONFIG = {
            'base_url': 'http://82.25.69.24:8090',
            'api_key': 'olvjg1k1ldmbhyl8owi6',
            'instance_name': 'marco_reunioes_bot'
        }
        
        evolution_api = EvolutionAPIReports(EVOLUTION_CONFIG)
        relatorio_dados = RelatorioDados('reunioes.db')
        gerador = GeradorRelatorios(evolution_api, relatorio_dados)
        
        # Menu de testes
        while True:
            print("\n📋 Escolha o tipo de relatório:")
            print("1. Resumo Semanal")
            print("2. Relatório Completo")
            print("3. Confirmações Pendentes")
            print("4. Enviar para WhatsApp")
            print("0. Sair")
            
            escolha = input("\nDigite sua opção: ").strip()
            
            if escolha == "1":
                relatorio = gerador.gerar_resumo_semanal()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "2":
                relatorio = gerador.gerar_relatorio_semanal_completo()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "3":
                relatorio = gerador.gerar_relatorio_confirmacoes_pendentes()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "4":
                telefone = input("Digite o telefone (ex: 21982161008): ").strip()
                if telefone:
                    print("Enviando resumo semanal...")
                    resultados = gerador.enviar_relatorio(
                        TipoRelatorio.RESUMO_SEMANAL, 
                        [telefone]
                    )
                    print(f"Resultado: {resultados}")
                
            elif escolha == "0":
                break
                
            else:
                print("❌ Opção inválida")
        
        print("👋 Teste finalizado!")
        
    except Exception as e:
        print(f"💥 Erro no teste: {e}")

    if __name__ == "__main__":
        import sys
        
        try:
            if len(sys.argv) > 1 and sys.argv[1] == "test":
                testar_relatorio_manual()
            else:
                main()
        except Exception as e:
            logger.error(f"Erro ao executar o programa: {e}")


    def _agendar_configuracao(self, config: ConfiguracaoRelatorio):
        """Agenda uma configuração específica"""
        try:
            def job_wrapper():
                self._executar_relatorio(config)
            
            # Agenda para cada dia da semana especificado
            for dia_semana in config.dias_semana:
                dia_nome = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][dia_semana]
                
                # Usa o método correto do schedule
                scheduler_job = getattr(schedule.every(), dia_nome)
                scheduler_job.at(config.horario_envio).do(job_wrapper)
                
                logger.info(f"📅 Agendado: {config.nome} - {dia_nome} às {config.horario_envio}")
                
        except Exception as e:
            logger.error(f"Erro ao agendar configuração {config.id}: {e}")

    def _executar_relatorio(self, config: ConfiguracaoRelatorio):
        """Executa um relatório específico"""
        try:
            logger.info(f"🚀 Executando relatório: {config.nome}")
            
            # Determina período baseado no tipo
            if config.tipo in [TipoRelatorio.SEMANAL_COMPLETO, TipoRelatorio.RESUMO_SEMANAL]:
                # Para relatórios semanais, usa semana atual
                data_inicio, data_fim = self.gerador_relatorios.relatorio_dados.get_semana_atual()
                resultados = self.gerador_relatorios.enviar_relatorio(
                    config.tipo, config.destinatarios, data_inicio, data_fim
                )
            else:
                # Para outros tipos, não precisa de período específico
                resultados = self.gerador_relatorios.enviar_relatorio(
                    config.tipo, config.destinatarios
                )
            
            # Log do resultado
            self.configurador.log_envio_relatorio(config.id, resultados)
            
            if resultados['success']:
                logger.info(f"✅ Relatório {config.nome} executado com sucesso")
            else:
                logger.error(f"❌ Falha no relatório {config.nome}: {resultados}")
                
        except Exception as e:
            logger.error(f"💥 Erro ao executar relatório {config.nome}: {e}")
            # Log do erro
            error_result = {
                'success': False,
                'enviados': 0,
                'falhas': len(config.destinatarios),
                'detalhes': [f"Erro interno: {str(e)}"]
            }
            self.configurador.log_envio_relatorio(config.id, error_result)

    def iniciar_scheduler(self):
        """Inicia o scheduler em loop contínuo"""
        self.running = True
        logger.info("🚀 Scheduler de relatórios iniciado")
        
        try:
            while self.running:
                # Reagenda relatórios a cada hora para pegar mudanças
                current_time = datetime.now()
                if current_time.minute == 0:  # A cada hora cheia
                    self.agendar_relatorios()
                
                # Executa tarefas pendentes
                schedule.run_pending()
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler interrompido pelo usuário")
        except Exception as e:
            logger.error(f"💥 Erro no scheduler: {e}")
        finally:
            self.running = False

    def parar_scheduler(self):
        """Para o scheduler"""
        self.running = False
        logger.info("🛑 Scheduler de relatórios parado")

def main():
    """Função principal do sistema de relatórios"""
    print("🚀 Iniciando Sistema de Relatórios Semanais...")
    
    try:
        # Configuração da Evolution API (mesma do app.py principal)
        EVOLUTION_CONFIG = {
            'base_url': 'http://82.25.69.24:8090',
            'api_key': 'olvjg1k1ldmbhyl8owi6',
            'instance_name': 'marco_reunioes_bot'
        }
        
        # Inicializa componentes
        evolution_api = EvolutionAPIReports(EVOLUTION_CONFIG)
        relatorio_dados = RelatorioDados('reunioes.db')  # Mesmo banco do app principal
        gerador = GeradorRelatorios(evolution_api, relatorio_dados)
        configurador = ConfiguradorRelatorios()
        scheduler = SchedulerRelatorios(gerador, configurador)
        
        print("✅ Componentes inicializados")
        
        # Testa relatório
        print("\n📊 Gerando relatório de teste...")
        relatorio_teste = gerador.gerar_resumo_semanal()
        print("Preview do relatório:")
        print("-" * 50)
        print(relatorio_teste[:300] + "...")
        print("-" * 50)
        
        # Inicia scheduler
        print("\n⏰ Iniciando scheduler automático...")
        scheduler.agendar_relatorios()
        
        print("📅 Relatórios agendados! Pressione Ctrl+C para parar.")
        scheduler.iniciar_scheduler()
        
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        logger.error(f"Erro crítico na inicialização: {e}")

def testar_relatorio_manual():
    """Função para testar geração manual de relatórios"""
    print("🧪 Teste Manual de Relatórios")
    
    try:
        EVOLUTION_CONFIG = {
            'base_url': 'http://82.25.69.24:8090',
            'api_key': 'olvjg1k1ldmbhyl8owi6',
            'instance_name': 'marco_reunioes_bot'
        }
        
        evolution_api = EvolutionAPIReports(EVOLUTION_CONFIG)
        relatorio_dados = RelatorioDados('reunioes.db')
        gerador = GeradorRelatorios(evolution_api, relatorio_dados)
        
        # Menu de testes
        while True:
            print("\n📋 Escolha o tipo de relatório:")
            print("1. Resumo Semanal")
            print("2. Relatório Completo")
            print("3. Confirmações Pendentes")
            print("4. Enviar para WhatsApp")
            print("0. Sair")
            
            escolha = input("\nDigite sua opção: ").strip()
            
            if escolha == "1":
                relatorio = gerador.gerar_resumo_semanal()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "2":
                relatorio = gerador.gerar_relatorio_semanal_completo()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "3":
                relatorio = gerador.gerar_relatorio_confirmacoes_pendentes()
                print("\n" + "="*60)
                print(relatorio)
                print("="*60)
                
            elif escolha == "4":
                telefone = input("Digite o telefone (ex: 21982161008): ").strip()
                if telefone:
                    print("Enviando resumo semanal...")
                    resultados = gerador.enviar_relatorio(
                        TipoRelatorio.RESUMO_SEMANAL, 
                        [telefone]
                    )
                    print(f"Resultado: {resultados}")
                
            elif escolha == "0":
                break
                
            else:
                print("❌ Opção inválida")
        
        print("👋 Teste finalizado!")
        
    except Exception as e:
        print(f"💥 Erro no teste: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        testar_relatorio_manual()
    else:
        main()