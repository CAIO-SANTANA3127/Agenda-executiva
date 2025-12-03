# cliente_autocomplete.py
"""
Módulo de autocomplete para clientes baseado em planilha Excel
Arquivo: clientes.xls na raiz do projeto
"""

import pandas as pd
import json
import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configuração de logging
logger = logging.getLogger(__name__)

# Cache global
_clientes_cache = None
_cache_timestamp = None
CLIENTES_FILE = 'clientes.xlsx'

def install_dependencies():
    """Instala dependências necessárias se não estiverem disponíveis"""
    try:
        import fuzzywuzzy
        from fuzzywuzzy import fuzz
    except ImportError:
        logger.info("Instalando fuzzywuzzy para busca inteligente...")
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "fuzzywuzzy[speedup]"])
            logger.info("fuzzywuzzy instalado com sucesso")
        except Exception as e:
            logger.warning(f"Erro ao instalar fuzzywuzzy: {e}")
            logger.info("Continuando sem fuzzywuzzy...")

# Tenta importar fuzzywuzzy, se não conseguir, usa busca simples
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logger.warning("fuzzywuzzy não disponível - usando busca simples")

def normalize_whatsapp(whatsapp_raw: str) -> str:
    """Normaliza número de WhatsApp para padrão brasileiro"""
    if not whatsapp_raw:
        return ""
    
    # Remove tudo exceto números
    whatsapp_clean = re.sub(r'\D', '', str(whatsapp_raw))
    
    if len(whatsapp_clean) < 10:
        return ""
    
    # Aplica regras de normalização brasileira
    if len(whatsapp_clean) == 10:
        # Formato antigo: 2182161008 -> 552198216100
        ddd = whatsapp_clean[:2]
        numero = whatsapp_clean[2:]
        return f"55{ddd}9{numero}"
    elif len(whatsapp_clean) == 11 and whatsapp_clean[2] == '9':
        # Formato atual: 21982161008 -> 5521982161008
        return f"55{whatsapp_clean}"
    elif len(whatsapp_clean) == 12 and whatsapp_clean.startswith('55'):
        # Formato antigo internacional: 552182161008 -> 5521982161008
        return f"{whatsapp_clean[:4]}9{whatsapp_clean[4:]}"
    elif len(whatsapp_clean) == 13 and whatsapp_clean.startswith('55'):
        # Já normalizado: 5521982161008
        return whatsapp_clean
    else:
        # Outros formatos: retorna como está se tiver pelo menos 10 dígitos
        return whatsapp_clean if len(whatsapp_clean) >= 10 else ""

def load_clientes_from_excel() -> List[Dict]:
    """Carrega dados dos clientes da planilha Excel com cache inteligente"""
    global _clientes_cache, _cache_timestamp
    
    try:
        current_time = datetime.now()
        
        # Verifica se arquivo existe
        if not os.path.exists(CLIENTES_FILE):
            logger.warning(f"Arquivo {CLIENTES_FILE} não encontrado na raiz do projeto")
            return []
        
        # Verifica timestamp do arquivo
        file_mtime = datetime.fromtimestamp(os.path.getmtime(CLIENTES_FILE))
        
        # Se cache existe e arquivo não foi modificado, retorna cache
        if (_clientes_cache is not None and 
            _cache_timestamp is not None and 
            file_mtime <= _cache_timestamp and
            (current_time - _cache_timestamp).seconds < 300):  # Cache válido por 5 minutos
            logger.debug("Usando cache de clientes")
            return _clientes_cache
        
        logger.info(f"Carregando clientes de {CLIENTES_FILE}")
        
        # Tenta carregar com diferentes engines
        df = None
        for engine in ['xlrd', 'openpyxl']:
            try:
                df = pd.read_excel(CLIENTES_FILE, engine=engine)
                logger.debug(f"Planilha carregada com engine: {engine}")
                break
            except Exception as e:
                logger.debug(f"Falha com engine {engine}: {e}")
                continue
        
        if df is None:
            logger.error("Não foi possível carregar a planilha com nenhuma engine")
            return []
        
        if df.empty:
            logger.warning("Planilha de clientes está vazia")
            return []
        
        # Normaliza nomes das colunas
        df.columns = df.columns.str.strip().str.upper()
        logger.info(f"Colunas encontradas: {list(df.columns)}")
        
        # Mapeia colunas obrigatórias
        column_map = {}
        required_fields = {
            'NOME': ['NOME', 'NAME', 'CLIENTE', 'PERSON', 'CONVIDADO', 'GUEST'],
            'EMPRESA': ['EMPRESA', 'COMPANY', 'CORPORACAO', 'NEGOCIO', 'BUSINESS'],
            'WHATSAPP': ['WHATSAPP', 'TELEFONE', 'PHONE', 'CELULAR', 'MOBILE', 'FONE', 'TEL']
        }
        
        for field, alternatives in required_fields.items():
            found_column = None
            for alt in alternatives:
                if alt in df.columns:
                    found_column = alt
                    break
            if found_column:
                column_map[field] = found_column
                logger.debug(f"Mapeado {field} -> {found_column}")
        
        # Verifica se pelo menos NOME foi encontrado
        if 'NOME' not in column_map:
            logger.error(f"Coluna NOME não encontrada. Colunas disponíveis: {list(df.columns)}")
            return []
        
        # Processa dados
        clientes = []
        processed_names = set()
        errors = 0
        
        for index, row in df.iterrows():
            try:
                # Extrai nome (obrigatório)
                nome_raw = str(row[column_map['NOME']]).strip()
                if not nome_raw or nome_raw.lower() in ['nan', 'none', '']:
                    continue
                
                # Verifica duplicatas por nome
                nome_upper = nome_raw.upper()
                if nome_upper in processed_names:
                    logger.debug(f"Nome duplicado ignorado: {nome_raw}")
                    continue
                processed_names.add(nome_upper)
                
                # Extrai empresa (opcional)
                empresa_raw = ""
                if 'EMPRESA' in column_map:
                    empresa_raw = str(row.get(column_map['EMPRESA'], '')).strip()
                    if empresa_raw.lower() in ['nan', 'none']:
                        empresa_raw = ""
                
                # Extrai WhatsApp (opcional)
                whatsapp_raw = ""
                whatsapp_normalized = ""
                if 'WHATSAPP' in column_map:
                    whatsapp_raw = str(row.get(column_map['WHATSAPP'], '')).strip()
                    if whatsapp_raw.lower() not in ['nan', 'none', '']:
                        whatsapp_normalized = normalize_whatsapp(whatsapp_raw)
                
                # Cria objeto cliente
                cliente = {
                    'id': len(clientes) + 1,
                    'nome': nome_raw,
                    'empresa': empresa_raw,
                    'whatsapp': whatsapp_normalized,
                    'whatsapp_original': whatsapp_raw,
                    # Campos para busca otimizada
                    'nome_search': nome_upper,
                    'empresa_search': empresa_raw.upper() if empresa_raw else '',
                    'search_combined': f"{nome_upper} {empresa_raw.upper()}".strip()
                }
                
                clientes.append(cliente)
                
            except Exception as e:
                errors += 1
                logger.debug(f"Erro ao processar linha {index + 1}: {e}")
                continue
        
        # Atualiza cache
        _clientes_cache = clientes
        _cache_timestamp = current_time
        
        logger.info(f"✅ {len(clientes)} clientes carregados com sucesso")
        if errors > 0:
            logger.warning(f"⚠️ {errors} linhas com erro foram ignoradas")
        
        return clientes
        
    except Exception as e:
        logger.error(f"Erro crítico ao carregar clientes: {e}")
        return []

def simple_fuzzy_score(text1: str, text2: str) -> int:
    """Implementação simples de fuzzy matching quando fuzzywuzzy não está disponível"""
    text1 = text1.upper()
    text2 = text2.upper()
    
    # Exact match
    if text1 == text2:
        return 100
    
    # Contains
    if text1 in text2 or text2 in text1:
        return 80
    
    # Word matching
    words1 = set(text1.split())
    words2 = set(text2.split())
    common_words = words1.intersection(words2)
    
    if common_words:
        ratio = len(common_words) / max(len(words1), len(words2))
        return int(ratio * 70)
    
    return 0

def search_clientes(query: str, limit: int = 10) -> List[Dict]:
    """Busca clientes por nome ou empresa com scoring inteligente"""
    if not query or len(query.strip()) < 2:
        return []
    
    clientes = load_clientes_from_excel()
    if not clientes:
        return []
    
    query_upper = query.upper().strip()
    results = []
    
    for cliente in clientes:
        score = 0
        match_reasons = []
        
        # 1. Busca exata por nome
        if query_upper == cliente['nome_search']:
            score += 1000
            match_reasons.append('nome_exato')
        elif query_upper in cliente['nome_search']:
            score += 500
            match_reasons.append('nome_contem')
        
        # 2. Busca por empresa
        if cliente['empresa_search']:
            if query_upper == cliente['empresa_search']:
                score += 800
                match_reasons.append('empresa_exata')
            elif query_upper in cliente['empresa_search']:
                score += 400
                match_reasons.append('empresa_contem')
        
        # 3. Busca por palavras individuais
        query_words = [w for w in query_upper.split() if len(w) >= 3]
        for word in query_words:
            if word in cliente['nome_search']:
                score += 200
                match_reasons.append('palavra_nome')
            if cliente['empresa_search'] and word in cliente['empresa_search']:
                score += 150
                match_reasons.append('palavra_empresa')
        
        # 4. Fuzzy matching (se disponível)
        if FUZZY_AVAILABLE:
            nome_fuzzy = fuzz.partial_ratio(query_upper, cliente['nome_search'])
            if nome_fuzzy >= 75:
                score += nome_fuzzy
                match_reasons.append('fuzzy_nome')
            
            if cliente['empresa_search']:
                empresa_fuzzy = fuzz.partial_ratio(query_upper, cliente['empresa_search'])
                if empresa_fuzzy >= 75:
                    score += int(empresa_fuzzy * 0.8)
                    match_reasons.append('fuzzy_empresa')
        else:
            # Fallback para fuzzy simples
            nome_simple = simple_fuzzy_score(query_upper, cliente['nome_search'])
            if nome_simple >= 60:
                score += nome_simple
                match_reasons.append('simple_nome')
            
            if cliente['empresa_search']:
                empresa_simple = simple_fuzzy_score(query_upper, cliente['empresa_search'])
                if empresa_simple >= 60:
                    score += int(empresa_simple * 0.8)
                    match_reasons.append('simple_empresa')
        
        # 5. Bonus por ter WhatsApp
        if cliente['whatsapp']:
            score += 10
        
        # Adiciona aos resultados se score mínimo
        if score >= 100:
            results.append({
                'cliente': cliente,
                'score': score,
                'match_reasons': match_reasons,
                'debug_info': {
                    'query': query_upper,
                    'nome_search': cliente['nome_search'],
                    'empresa_search': cliente['empresa_search']
                }
            })
    
    # Ordena por score decrescente
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Log de debug
    if results:
        logger.debug(f"Busca '{query}' retornou {len(results)} resultados")
        for i, r in enumerate(results[:3]):  # Log dos 3 primeiros
            logger.debug(f"  {i+1}. {r['cliente']['nome']} (score: {r['score']}, reasons: {r['match_reasons']})")
    
    return [r['cliente'] for r in results[:limit]]

def get_clientes_stats() -> Dict:
    """Retorna estatísticas dos clientes carregados"""
    clientes = load_clientes_from_excel()
    
    if not clientes:
        return {
            'total_clientes': 0,
            'com_empresa': 0,
            'com_whatsapp': 0,
            'sem_telefone': 0,
            'empresas_unicas': 0,
            'cache_info': 'Nenhum cliente carregado'
        }
    
    stats = {
        'total_clientes': len(clientes),
        'com_empresa': len([c for c in clientes if c['empresa']]),
        'com_whatsapp': len([c for c in clientes if c['whatsapp']]),
        'sem_telefone': len([c for c in clientes if not c['whatsapp']]),
        'empresas_unicas': len(set(c['empresa'] for c in clientes if c['empresa'])),
        'cache_info': f"Cache atualizado: {_cache_timestamp.strftime('%H:%M:%S') if _cache_timestamp else 'N/A'}"
    }
    
    return stats

def clear_cache():
    """Limpa o cache de clientes"""
    global _clientes_cache, _cache_timestamp
    _clientes_cache = None
    _cache_timestamp = None
    logger.info("Cache de clientes limpo")

def validate_clientes_file() -> Dict:
    """Valida se o arquivo de clientes está acessível e bem formatado"""
    validation = {
        'file_exists': False,
        'file_readable': False,
        'columns_ok': False,
        'has_data': False,
        'errors': [],
        'file_info': {}
    }
    
    try:
        # Verifica se arquivo existe
        if not os.path.exists(CLIENTES_FILE):
            validation['errors'].append(f"Arquivo {CLIENTES_FILE} não encontrado")
            return validation
        
        validation['file_exists'] = True
        
        # Info do arquivo
        stat = os.stat(CLIENTES_FILE)
        validation['file_info'] = {
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
        }
        
        # Tenta ler arquivo
        try:
            df = pd.read_excel(CLIENTES_FILE)
            validation['file_readable'] = True
            
            # Verifica colunas
            df.columns = df.columns.str.strip().str.upper()
            required_cols = ['NOME']
            optional_cols = ['EMPRESA', 'WHATSAPP', 'TELEFONE']
            
            found_required = [col for col in required_cols if col in df.columns]
            found_optional = [col for col in optional_cols if col in df.columns]
            
            if found_required:
                validation['columns_ok'] = True
            else:
                validation['errors'].append(f"Coluna obrigatória NOME não encontrada. Colunas: {list(df.columns)}")
            
            # Verifica dados
            if not df.empty:
                validation['has_data'] = True
                validation['file_info']['total_rows'] = len(df)
                validation['file_info']['columns'] = list(df.columns)
                validation['file_info']['required_found'] = found_required
                validation['file_info']['optional_found'] = found_optional
            else:
                validation['errors'].append("Planilha está vazia")
                
        except Exception as e:
            validation['errors'].append(f"Erro ao ler planilha: {str(e)}")
            
    except Exception as e:
        validation['errors'].append(f"Erro ao acessar arquivo: {str(e)}")
    
    return validation

# Função de inicialização (chamada automaticamente na importação)
def init_module():
    """Inicializa o módulo de autocomplete"""
    logger.info("🔍 Módulo de autocomplete de clientes inicializado")
    
    # Instala dependências se necessário
    install_dependencies()
    
    # Valida arquivo de clientes
    validation = validate_clientes_file()
    
    if validation['file_exists']:
        logger.info(f"✅ Arquivo {CLIENTES_FILE} encontrado")
        if validation['has_data']:
            # Faz um pré-carregamento para validar
            clientes = load_clientes_from_excel()
            logger.info(f"📊 {len(clientes)} clientes disponíveis para autocomplete")
        else:
            logger.warning(f"⚠️ Arquivo {CLIENTES_FILE} existe mas tem problemas: {validation['errors']}")
    else:
        logger.warning(f"⚠️ Arquivo {CLIENTES_FILE} não encontrado na raiz do projeto")
        logger.info("💡 Crie o arquivo clientes.xls com colunas: NOME, EMPRESA, WHATSAPP")

# Executa inicialização ao importar
init_module()