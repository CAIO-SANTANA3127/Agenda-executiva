/**
 * ================================================
 * SISTEMA DE GESTÃO DE EVENTOS v1.0
 * ================================================
 * Gerenciamento completo de eventos da empresa
 */

class EventosManager {
    constructor(agendaInstance) {
        this.agenda = agendaInstance;
        this.eventos = [];
        this.editingEventoId = null;
        
        this.init();
    }
    
    init() {
        console.log('🎉 EventosManager inicializado');
        this.loadEventos();
    }
    
    // ================================================
    // CARREGAR EVENTOS
    // ================================================
    async loadEventos() {
        try {
            const response = await fetch('/api/eventos/list');
            const data = await response.json();
            
            if (data.success) {
                this.eventos = data.eventos || [];
                Logger.log(`${this.eventos.length} eventos carregados`, 'success');
                this.renderEventos();
            }
        } catch (error) {
            Logger.handleError('Erro ao carregar eventos', error);
        }
    }
    
    // ================================================
    // SALVAR EVENTO
    // ================================================
    async salvarEvento() {
        const formData = this.coletarDadosFormulario();
        
        // Validação
        const erros = this.validarEvento(formData);
        if (erros.length > 0) {
            NotificationManager.show(erros.join('\n'), 'error');
            return;
        }
        
        try {
            const url = this.editingEventoId 
                ? `/api/eventos/editar/${this.editingEventoId}`
                : '/api/eventos/criar';
            
            const method = this.editingEventoId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                NotificationManager.show(data.message || 'Evento salvo com sucesso!', 'success');
                this.fecharModal();
                this.loadEventos();
                
                // Atualiza agenda principal
                if (this.agenda && typeof this.agenda.applyFilters === 'function') {
                    this.agenda.applyFilters();
                }
            } else {
                throw new Error(data.message || 'Erro ao salvar evento');
            }
        } catch (error) {
            Logger.handleError('Erro ao salvar evento', error);
        }
    }
    
    // ================================================
    // EDITAR EVENTO
    // ================================================
    editarEvento(eventoId) {
        const evento = this.eventos.find(e => e.id === eventoId);
        if (!evento) {
            NotificationManager.show('Evento não encontrado', 'error');
            return;
        }
        
        this.editingEventoId = eventoId;
        
        // Preenche formulário
        document.getElementById('evento_titulo').value = evento.titulo || '';
        document.getElementById('evento_tipo').value = evento.tipo || '';
        document.getElementById('evento_data_inicio').value = evento.data_inicio || '';
        document.getElementById('evento_data_fim').value = evento.data_fim || '';
        document.getElementById('evento_local').value = evento.local || '';
        document.getElementById('evento_descricao').value = evento.descricao || '';
        document.getElementById('evento_participantes').value = evento.participantes || '';
        document.getElementById('evento_cor').value = evento.cor || 'amarelo';
        
        // Atualiza título do modal
        document.getElementById('modalEventoTitle').innerHTML = '<i class="fas fa-edit"></i> Editar Evento';
        document.getElementById('submitEventoText').textContent = 'Atualizar Evento';
        
        this.abrirModal();
    }
    
    // ================================================
    // EXCLUIR EVENTO
    // ================================================
    async excluirEvento(eventoId, titulo) {
        if (!confirm(`Deseja realmente excluir o evento "${titulo}"?\n\nEsta ação não pode ser desfeita.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/eventos/excluir/${eventoId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                NotificationManager.show('Evento excluído com sucesso!', 'success');
                this.loadEventos();
                
                // Atualiza agenda principal
                if (this.agenda && typeof this.agenda.applyFilters === 'function') {
                    this.agenda.applyFilters();
                }
            } else {
                throw new Error(data.message || 'Erro ao excluir evento');
            }
        } catch (error) {
            Logger.handleError('Erro ao excluir evento', error);
        }
    }
    
    // ================================================
    // RENDERIZAR EVENTOS
    // ================================================
    renderEventos() {
        if (!this.agenda || !this.agenda.elements || !this.agenda.elements.meetingsGrid) {
            console.warn('Grid não disponível para renderizar eventos');
            return;
        }
        
        // Os eventos serão renderizados junto com as reuniões
        // no grid principal pela função applyFilters da agenda
        console.log(`Eventos prontos para renderização: ${this.eventos.length}`);
    }
    
    // ================================================
    // GERAR HTML DO CARD DE EVENTO
    // ================================================
    gerarCardHTML(evento) {
        const dataInicio = new Date(evento.data_inicio);
        const dataFim = new Date(evento.data_fim);
        
        const dataInicioFormatada = dataInicio.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        
        const dataFimFormatada = dataFim.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        
        const horaInicio = dataInicio.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const horaFim = dataFim.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Calcula duração
        const duracao = this.calcularDuracao(dataInicio, dataFim);
        
        // Ícone do tipo
        const tipoIcons = {
            'viagem': '🧳',
            'feira': '🏢',
            'conferencia': '🎤',
            'treinamento': '📚',
            'evento_interno': '🎉',
            'outro': '📌'
        };
        
        const icone = tipoIcons[evento.tipo] || '📅';
        const corClass = `cor-${evento.cor || 'amarelo'}`;
        
        return `
            <div class="meeting-card evento-card ${corClass}" data-evento-id="${evento.id}">
                <div class="meeting-header">
                    <h3 class="meeting-title">${icone} ${evento.titulo}</h3>
                    <div class="meeting-badges">
                        <span class="evento-tipo-badge">
                            ${evento.tipo.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>
                </div>
                
                <div class="meeting-info">
                    <div class="evento-duracao">
                        <i class="fas fa-clock"></i>
                        <span>${duracao}</span>
                    </div>
                    
                    <div class="info-item">
                        <i class="fas fa-calendar-alt"></i>
                        <span><strong>Início:</strong> ${dataInicioFormatada}, ${horaInicio}</span>
                    </div>
                    
                    <div class="info-item">
                        <i class="fas fa-calendar-check"></i>
                        <span><strong>Fim:</strong> ${dataFimFormatada}, ${horaFim}</span>
                    </div>
                    
                    ${evento.local ? `
                        <div class="info-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${evento.local}</span>
                        </div>
                    ` : ''}
                    
                    ${evento.participantes ? `
                        <div class="info-item">
                            <i class="fas fa-users"></i>
                            <span>${evento.participantes}</span>
                        </div>
                    ` : ''}
                    
                    ${evento.descricao ? `
                        <div class="info-item">
                            <i class="fas fa-align-left"></i>
                            <span>${evento.descricao.substring(0, 100)}${evento.descricao.length > 100 ? '...' : ''}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="meeting-actions">
                    <button class="btn-action btn-evento-action" onclick="eventosManager.editarEvento(${evento.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn-action btn-delete" onclick="eventosManager.excluirEvento(${evento.id}, '${evento.titulo.replace(/'/g, "\\'")}')">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        `;
    }
    
    // ================================================
    // UTILITÁRIOS
    // ================================================
    calcularDuracao(inicio, fim) {
        const diff = fim - inicio;
        const dias = Math.floor(diff / (1000 * 60 * 60 * 24));
        const horas = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (dias > 0) {
            return `${dias} dia${dias > 1 ? 's' : ''} e ${horas}h`;
        } else {
            return `${horas} hora${horas !== 1 ? 's' : ''}`;
        }
    }
    
    coletarDadosFormulario() {
        return {
            titulo: document.getElementById('evento_titulo').value.trim(),
            tipo: document.getElementById('evento_tipo').value,
            data_inicio: document.getElementById('evento_data_inicio').value,
            data_fim: document.getElementById('evento_data_fim').value,
            local: document.getElementById('evento_local').value.trim(),
            descricao: document.getElementById('evento_descricao').value.trim(),
            participantes: document.getElementById('evento_participantes').value.trim(),
            cor: document.getElementById('evento_cor').value
        };
    }
    
    validarEvento(data) {
        const erros = [];
        
        if (!data.titulo) erros.push('Título é obrigatório');
        if (!data.tipo) erros.push('Tipo de evento é obrigatório');
        if (!data.data_inicio) erros.push('Data/hora início é obrigatória');
        if (!data.data_fim) erros.push('Data/hora fim é obrigatória');
        
        if (data.data_inicio && data.data_fim) {
            const inicio = new Date(data.data_inicio);
            const fim = new Date(data.data_fim);
            
            if (fim <= inicio) {
                erros.push('Data/hora fim deve ser posterior à data/hora início');
            }
        }
        
        return erros;
    }
    
    // ================================================
    // MODAL
    // ================================================
    abrirModal() {
        const modal = document.getElementById('modalEvento');
        if (modal) {
            modal.style.display = 'flex';
            document.getElementById('evento_titulo')?.focus();
        }
    }
    
    fecharModal() {
        const modal = document.getElementById('modalEvento');
        if (modal) {
            modal.style.display = 'none';
        }
        
        this.resetarFormulario();
        this.editingEventoId = null;
    }
    
    resetarFormulario() {
        document.getElementById('formEvento')?.reset();
        document.getElementById('modalEventoTitle').innerHTML = '<i class="fas fa-calendar-alt"></i> Novo Evento';
        document.getElementById('submitEventoText').textContent = 'Salvar Evento';
    }
}

// ================================================
// FUNÇÕES GLOBAIS
// ================================================
let eventosManager;

function abrirModalEvento() {
    if (eventosManager) {
        eventosManager.abrirModal();
    }
}

function fecharModalEvento() {
    if (eventosManager) {
        eventosManager.fecharModal();
    }
}

function salvarEvento() {
    if (eventosManager) {
        eventosManager.salvarEvento();
    }
}

// ================================================
// INICIALIZAÇÃO
// ================================================
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda agenda estar pronta
    setTimeout(() => {
        if (typeof agenda !== 'undefined') {
            eventosManager = new EventosManager(agenda);
            window.eventosManager = eventosManager;
            console.log('✅ Sistema de Eventos inicializado');
        }
    }, 2000);
});