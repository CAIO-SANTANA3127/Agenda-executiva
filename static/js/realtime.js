/**
 * ========================================================
 * CLIENTE WEBSOCKET PARA ATUALIZAÇÃO EM TEMPO REAL
 * ========================================================
 * Conecta com a API de webhook e atualiza interface automaticamente
 */

class RealtimeMeetingClient {
    constructor(socketUrl = 'http://localhost:5001') {
        this.socketUrl = socketUrl;
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.subscribedMeetings = new Set();
        
        this.init();
    }

    /**
     * Inicializa conexão WebSocket
     */
    init() {
        try {
            console.log('🔌 Conectando ao servidor WebSocket...');
            
            // Inclui biblioteca Socket.IO
            if (typeof io === 'undefined') {
                console.error('❌ Socket.IO não carregado. Inclua: <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>');
                return;
            }
            
            this.socket = io(this.socketUrl, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: this.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts
            });
            
            this.setupEventListeners();
            
        } catch (error) {
            console.error('❌ Erro ao inicializar WebSocket:', error);
        }
    }

    /**
     * Configura listeners de eventos
     */
    setupEventListeners() {
        // Conexão estabelecida
        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log('✅ Conectado ao servidor WebSocket');
            this.showNotification('Conectado ao servidor de notificações', 'success');
            
            // Re-inscreve em reuniões que estava monitorando
            this.resubscribeToMeetings();
        });

        // Conexão perdida
        this.socket.on('disconnect', (reason) => {
            this.connected = false;
            console.warn('⚠️ Desconectado:', reason);
            this.showNotification('Conexão com servidor perdida', 'warning');
        });

        // Erro de conexão
        this.socket.on('connect_error', (error) => {
            console.error('❌ Erro de conexão:', error);
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.showNotification('Falha ao conectar ao servidor', 'error');
            }
        });

        // EVENTO: Reunião atualizada
        this.socket.on('meeting_update', (data) => {
            console.log('📥 Atualização de reunião recebida:', data);
            this.handleMeetingUpdate(data);
        });

        // EVENTO: Nova resposta
        this.socket.on('new_response', (data) => {
            console.log('📬 Nova resposta recebida:', data);
            this.handleNewResponse(data);
        });

        // Confirmação de inscrição
        this.socket.on('joined_meeting', (data) => {
            console.log('✅ Inscrito na reunião:', data.meeting_id);
        });

        // Pong (keep-alive)
        this.socket.on('pong', (data) => {
            console.debug('🏓 Pong recebido:', data.timestamp);
        });
    }

    /**
     * Inscreve-se para receber atualizações de uma reunião específica
     */
    subscribeMeeting(meetingId) {
        if (!this.connected) {
            console.warn('⚠️ WebSocket não conectado. Tentando inscrever após conectar...');
            this.subscribedMeetings.add(meetingId);
            return;
        }

        try {
            this.socket.emit('join_meeting', { meeting_id: meetingId });
            this.subscribedMeetings.add(meetingId);
            console.log(`📥 Inscrito para receber atualizações da reunião ${meetingId}`);
        } catch (error) {
            console.error('Erro ao inscrever:', error);
        }
    }

    /**
     * Re-inscreve em reuniões após reconexão
     */
    resubscribeToMeetings() {
        this.subscribedMeetings.forEach(meetingId => {
            this.socket.emit('join_meeting', { meeting_id: meetingId });
        });
    }

    /**
     * Manipula atualização de reunião
     */
    handleMeetingUpdate(data) {
        const meetingId = data.meeting_id;
        const meetingData = data.data.meeting;
        const responses = data.data.responses;

        console.log(`🔄 Processando atualização da reunião ${meetingId}`);

        // 1. Atualiza card no grid principal
        this.updateMeetingCard(meetingId, meetingData);

        // 2. Atualiza modal de detalhes (se estiver aberto)
        this.updateMeetingDetailsModal(meetingId, meetingData, responses);

        // 3. Mostra notificação
        this.showUpdateNotification(meetingData);

        // 4. Atualiza contadores
        this.updateStatusCounters();

        // 5. CALLBACK CUSTOMIZADO (se definido pelo usuário)
        if (typeof window.onMeetingUpdated === 'function') {
            window.onMeetingUpdated(meetingId, meetingData, responses);
        }
    }

    /**
     * Manipula nova resposta
     */
    handleNewResponse(data) {
        const meetingId = data.meeting_id;
        const response = data.response;

        console.log(`💬 Nova resposta para reunião ${meetingId}:`, response);

        // Atualiza interface
        this.addResponseToUI(meetingId, response);

        // Notificação
        this.showNotification(
            `Nova resposta recebida: ${response.response?.status || 'Resposta processada'}`,
            'info'
        );

        // CALLBACK CUSTOMIZADO
        if (typeof window.onNewResponse === 'function') {
            window.onNewResponse(meetingId, response);
        }
    }

    /**
     * Atualiza card da reunião no grid
     */
    updateMeetingCard(meetingId, meetingData) {
        try {
            // Busca o card da reunião
            const cardSelector = `.meeting-card[data-meeting-id="${meetingId}"]`;
            let card = document.querySelector(cardSelector);

            if (!card) {
                // Tenta alternativa: botões com onclick contendo o ID
                const buttons = document.querySelectorAll('button[onclick*="openMeetingDetailsModal"]');
                for (const btn of buttons) {
                    const onclick = btn.getAttribute('onclick');
                    if (onclick && onclick.includes(`(${meetingId})`)) {
                        card = btn.closest('.meeting-card');
                        break;
                    }
                }
            }

            if (card) {
                // Atualiza badge de status
                const statusBadge = card.querySelector('.confirmation-status');
                if (statusBadge) {
                    const newStatus = meetingData.status_confirmacao || 'pending';
                    statusBadge.className = `confirmation-status status-${newStatus}`;
                    statusBadge.textContent = this.getStatusText(newStatus);

                    // Animação de destaque
                    card.style.transition = 'all 0.5s ease';
                    card.style.transform = 'scale(1.02)';
                    card.style.boxShadow = '0 8px 24px rgba(16, 185, 129, 0.4)';
                    card.style.borderColor = '#10b981';

                    setTimeout(() => {
                        card.style.transform = '';
                        card.style.boxShadow = '';
                        card.style.borderColor = '';
                    }, 2000);
                }

                console.log(`✅ Card da reunião ${meetingId} atualizado`);
            } else {
                console.warn(`⚠️ Card da reunião ${meetingId} não encontrado`);
            }

        } catch (error) {
            console.error('Erro ao atualizar card:', error);
        }
    }

    /**
     * Atualiza modal de detalhes (se estiver aberto)
     */
    updateMeetingDetailsModal(meetingId, meetingData, responses) {
        try {
            const modal = document.getElementById('meetingDetailsModal');
            
            // Verifica se o modal está aberto E é desta reunião
            if (modal && (modal.style.display === 'block' || modal.style.display === 'flex')) {
                // Verifica se é a mesma reunião (usando variável global ou data-attribute)
                const currentMeetingId = window.currentOpenMeetingId || 
                                        modal.getAttribute('data-meeting-id');

                if (parseInt(currentMeetingId) === parseInt(meetingId)) {
                    console.log(`🔄 Atualizando modal da reunião ${meetingId}`);
                    
                    // Re-renderiza os detalhes
                    if (window.agenda && typeof window.agenda.renderMeetingDetails === 'function') {
                        window.agenda.renderMeetingDetails(meetingData, responses);
                        
                        // Animação visual
                        const statusElements = modal.querySelectorAll('.confirmation-status');
                        statusElements.forEach(el => {
                            el.style.transition = 'all 0.5s ease';
                            el.style.background = '#dcfce7';
                            el.style.boxShadow = '0 0 12px rgba(16, 185, 129, 0.4)';
                            
                            setTimeout(() => {
                                el.style.background = '';
                                el.style.boxShadow = '';
                            }, 1500);
                        });
                    }
                }
            }

        } catch (error) {
            console.error('Erro ao atualizar modal:', error);
        }
    }

    /**
     * Adiciona resposta na UI
     */
    addResponseToUI(meetingId, response) {
        try {
            const modal = document.getElementById('meetingDetailsModal');
            if (!modal || modal.style.display === 'none') return;

            const responsesContainer = modal.querySelector('.responses-container');
            if (responsesContainer) {
                const responseHTML = this.generateResponseHTML(response.response);
                responsesContainer.insertAdjacentHTML('afterbegin', responseHTML);
            }

        } catch (error) {
            console.error('Erro ao adicionar resposta:', error);
        }
    }

    /**
     * Gera HTML de resposta
     */
    generateResponseHTML(response) {
        return `
            <div class="response-item status-${response.status}" style="animation: slideIn 0.3s ease;">
                <div class="response-header">
                    <span class="response-status">${this.getStatusText(response.status)}</span>
                    <span class="response-time">${new Date(response.received_at).toLocaleString('pt-BR')}</span>
                    <span class="response-confidence">Confiança: ${Math.round(response.confidence * 100)}%</span>
                </div>
                <div class="response-text">${response.response_text}</div>
            </div>
        `;
    }

    /**
     * Atualiza contadores de status
     */
    updateStatusCounters() {
        // Se você tem contadores na interface, atualiza aqui
        // Exemplo:
        // document.getElementById('total-confirmed').textContent = confirmedCount;
    }

    /**
     * Mostra notificação de atualização
     */
    showUpdateNotification(meetingData) {
        const status = meetingData.status_confirmacao;
        const statusText = this.getStatusText(status);
        
        let message = `Reunião "${meetingData.titulo}" atualizada: ${statusText}`;
        let type = 'info';
        
        if (status === 'confirmed') {
            type = 'success';
        } else if (status === 'declined') {
            type = 'error';
        }
        
        this.showNotification(message, type);
    }

    /**
     * Mostra notificação na tela
     */
    showNotification(message, type = 'info') {
        // Se você usa toastr
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
        } 
        // Se você usa NotificationManager
        else if (typeof NotificationManager !== 'undefined') {
            NotificationManager.show(message, type);
        }
        // Fallback: console
        else {
            const icon = {
                'success': '✅',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            }[type] || 'ℹ️';
            console.log(`${icon} ${message}`);
        }
    }

    /**
     * Traduz status para texto
     */
    getStatusText(status) {
        const statusMap = {
            'confirmed': 'Confirmada',
            'declined': 'Recusada',
            'pending': 'Pendente',
            'unclear': 'Não Clara',
            'reschedule': 'Reagendar'
        };
        return statusMap[status] || 'Pendente';
    }

    /**
     * Busca status via API REST (fallback)
     */
    async fetchMeetingStatus(meetingId) {
        try {
            const response = await fetch(`${this.socketUrl}/api/meetings/${meetingId}/status`);
            const data = await response.json();
            
            if (data.success) {
                return data;
            } else {
                throw new Error(data.message || 'Erro ao buscar status');
            }
        } catch (error) {
            console.error('Erro ao buscar status:', error);
            return null;
        }
    }

    /**
     * Busca atualizações recentes
     */
    async fetchRecentUpdates() {
        try {
            const response = await fetch(`${this.socketUrl}/api/meetings/recent-updates`);
            const data = await response.json();
            
            if (data.success) {
                return data.updates;
            }
            return [];
        } catch (error) {
            console.error('Erro ao buscar atualizações:', error);
            return [];
        }
    }

    /**
     * Desconecta WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
            console.log('🔌 Desconectado do WebSocket');
        }
    }

    /**
     * Verifica se está conectado
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
}

// ========================================================
// INICIALIZAÇÃO AUTOMÁTICA
// ========================================================

// Instância global
let realtimeClient = null;

// Inicializa quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('🚀 Iniciando cliente de tempo real...');
        
        // Cria instância
        realtimeClient = new RealtimeMeetingClient('http://localhost:5001');
        
        // Expõe globalmente
        window.realtimeClient = realtimeClient;
        
        console.log('✅ Cliente de tempo real inicializado');
        console.log('💡 Use: realtimeClient.subscribeMeeting(meetingId) para monitorar uma reunião');
        
    } catch (error) {
        console.error('❌ Erro ao inicializar cliente de tempo real:', error);
    }
});

// ========================================================
// CALLBACKS CUSTOMIZÁVEIS (OPCIONAL)
// ========================================================

/**
 * Você pode definir estes callbacks no seu código:
 * 
 * window.onMeetingUpdated = function(meetingId, meetingData, responses) {
 *     // Seu código customizado aqui
 * };
 * 
 * window.onNewResponse = function(meetingId, response) {
 *     // Seu código customizado aqui
 * };
 */

// ========================================================
// CSS PARA ANIMAÇÕES
// ========================================================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .response-item {
        animation: slideIn 0.3s ease;
    }
`;
document.head.appendChild(style);