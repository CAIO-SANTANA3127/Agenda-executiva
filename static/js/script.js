/**
 * ================================================
 * AGENDA EXECUTIVA - SISTEMA PROFISSIONAL v4.2
 * ================================================
 * Código reorganizado e otimizado
 * Estrutura modular e livre de erros
 */

// ================================================
// UTILITÁRIOS E HELPERS
// ================================================
class Utils {
    static ensureString(value) {
        if (value == null) return '';
        if (typeof value === 'string') return value;
        return String(value);
    }

    static sanitizeInput(input) {
        if (input == null) return '';
        if (typeof input === 'string') {
            return input.trim().replace(/[<>]/g, '');
        }
        return String(input).trim().replace(/[<>]/g, '');
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static formatPhone(phone) {
        if (!phone) return '';
        const clean = phone.replace(/\D/g, '');
        
        if (clean.length === 13 && clean.startsWith('55')) {
            const ddd = clean.substring(2, 4);
            const number = clean.substring(4);
            return `+55 (${ddd}) ${number.substring(0, 5)}-${number.substring(5)}`;
        }
        
        if (clean.length === 11) {
            const ddd = clean.substring(0, 2);
            const number = clean.substring(2);
            return `(${ddd}) ${number.substring(0, 5)}-${number.substring(5)}`;
        }
        
        return phone;
    }

    static formatDateTime(datetime) {
        try {
            const date = new Date(datetime);
            if (isNaN(date.getTime())) {
                throw new Error('Data inválida');
            }

            const daysOfWeek = [
                'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 
                'Quinta-feira', 'Sexta-feira', 'Sábado'
            ];
            const daysOfWeekShort = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

            const dayOfWeek = daysOfWeek[date.getDay()];
            const dayOfWeekShort = daysOfWeekShort[date.getDay()];

            const formattedDate = date.toLocaleDateString('pt-BR', {
                day: '2-digit', 
                month: '2-digit', 
                year: 'numeric'
            });

            const formattedTime = date.toLocaleTimeString('pt-BR', {
                hour: '2-digit', 
                minute: '2-digit'
            });

            return {
                full: `${dayOfWeek}, ${formattedDate}, ${formattedTime}`,
                compact: `${dayOfWeekShort}, ${formattedDate}, ${formattedTime}`,
                dateOnly: formattedDate,
                timeOnly: formattedTime,
                weekday: dayOfWeek,
                weekdayShort: dayOfWeekShort,
                original: date.toLocaleString('pt-BR', {
                    day: '2-digit', 
                    month: '2-digit', 
                    year: 'numeric',
                    hour: '2-digit', 
                    minute: '2-digit'
                })
            };
        } catch (error) {
            console.error(`Erro ao formatar data: ${datetime}`, error);
            return {
                full: 'Data inválida',
                compact: 'Data inválida',
                dateOnly: 'Data inválida',
                timeOnly: 'Data inválida',
                weekday: 'Data inválida',
                weekdayShort: 'Data inválida',
                original: 'Data inválida'
            };
        }
    }

    static getWeekNumber(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
    }

    static getCurrentWeekInfo() {
        const now = new Date();
        const startOfWeek = new Date(now);
        startOfWeek.setDate(now.getDate() - now.getDay());
        
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        
        const startFormatted = startOfWeek.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit' 
        });
        const endFormatted = endOfWeek.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
        });
        
        return `Semana atual: ${startFormatted} a ${endFormatted}`;
    }
}

// ================================================
// LOGGER SISTEMA
// ================================================
class Logger {
    static log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}] ${message}`;
        
        switch (type) {
            case 'error':
                console.error(logMessage);
                break;
            case 'warn':
                console.warn(logMessage);
                break;
            case 'success':
                console.log(`✅ ${logMessage}`);
                break;
            default:
                console.log(logMessage);
        }
    }

    static handleError(message, error = null) {
        this.log(`${message}: ${error?.message || 'Erro desconhecido'}`, 'error');
        
        if (error?.stack) {
            console.error(error.stack);
        }
        
        NotificationManager.show(message, 'error');
    }
}

// ================================================
// GERENCIADOR DE NOTIFICAÇÕES
// ================================================
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        console.log(`${icons[type] || icons.info} ${message}`);
        
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
        } else {
            alert(`${icons[type] || icons.info} ${message}`);
        }
    }
}

// ================================================
// GERENCIADOR DE API
// ================================================
class ApiManager {
    constructor() {
        this.maxRetries = 3;
        this.retryDelay = 2000;
    }

    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        let lastError;

        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, defaultOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                return data;
                
            } catch (error) {
                lastError = error;
                
                if (error.name === 'TypeError') {
                    lastError = new Error('Erro de conexão. Verifique sua internet.');
                }
                
                if (attempt < this.maxRetries) {
                    Logger.log(`Tentativa ${attempt} falhou, tentando novamente...`, 'warn');
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                }
            }
        }

        throw lastError;
    }
}

// ================================================
// GERENCIADOR DE MODAIS
// ================================================
class ModalManager {
    constructor() {
        this.openModals = new Set();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAll();
            }
        });

        window.addEventListener('click', (event) => {
            const modals = ['modal', 'whatsappModal', 'messageTemplateModal', 'whatsappStatusModal', 'meetingDetailsModal'];
            
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (modal && event.target === modal) {
                    this.close(modalId);
                }
            });
        });
    }

    open(modalId, onOpen = null) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            this.openModals.add(modalId);
            
            if (onOpen) {
                setTimeout(onOpen, 100);
            }
        }
    }

    close(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            this.openModals.delete(modalId);
        }
    }

    closeAll() {
        this.openModals.forEach(modalId => this.close(modalId));
    }

    isOpen(modalId) {
        return this.openModals.has(modalId);
    }
}

// ================================================
// VALIDADOR DE FORMULÁRIOS
// ================================================
class FormValidator {
    static validateMeetingData(data) {
        const errors = [];

        const requiredFields = {
            'Título': data.titulo,
            'Convidado': data.convidado,
            'Data/Hora': data.data_hora,
            'Assunto': data.assunto
        };

        errors.push(...this.validateRequired(requiredFields));

        // Validação de telefone para auto-send
        if (data.auto_send_whatsapp && !data.editing) {
            if (!data.telefone_cliente || !data.telefone_cliente.trim()) {
                errors.push('Para envio automático de WhatsApp, é necessário informar o telefone do cliente');
            } else {
                const cleanPhone = data.telefone_cliente.replace(/\D/g, '');
                if (cleanPhone.length < 10) {
                    errors.push('Telefone deve ter pelo menos 10 dígitos para envio automático');
                }
            }
        }

        // Validação de data/hora
        if (data.data_hora) {
            const meetingDate = new Date(data.data_hora);
            if (isNaN(meetingDate.getTime())) {
                errors.push('Data/hora inválida');
            } else if (!data.editing) {
                const now = new Date();
                if (meetingDate < now) {
                    errors.push('A data da reunião não pode ser no passado');
                }
            }
        }

        return errors;
    }

    static validateRequired(fields) {
        const errors = [];
        
        Object.entries(fields).forEach(([name, value]) => {
            const stringValue = Utils.ensureString(value);
            if (!stringValue || !stringValue.trim()) {
                errors.push(`Campo ${name} é obrigatório`);
            }
        });
        
        return errors;
    }

    static validateWhatsAppData(data) {
        const errors = [];

        if (!data.phoneNumber) {
            errors.push('Por favor, digite um número de WhatsApp válido');
        } else {
            const cleanPhone = data.phoneNumber.replace(/\D/g, '');
            if (cleanPhone.length < 10) {
                errors.push('Número de telefone deve ter pelo menos 10 dígitos');
            }
        }

        if (!data.message) {
            errors.push('Por favor, digite uma mensagem');
        }

        if (data.sendType === 'whatsapp_web' && !data.meetingId) {
            errors.push('Para envio via WhatsApp Web, selecione uma reunião');
        }

        return errors;
    }
}

// ================================================
// AUTOCOMPLETE DE CLIENTES
// ================================================
class ClientAutocomplete {
    constructor(inputId, suggestionsId) {
        this.input = document.getElementById(inputId);
        this.suggestionsContainer = document.getElementById(suggestionsId);
        this.currentFocus = -1;
        this.selectedClient = null;
        this.searchTimeout = null;
        this.cache = new Map();
        this.activeModalMeetingId = null;
        
        if (this.input && this.suggestionsContainer) {
            this.init();
            Logger.log('Autocomplete inicializado', 'success');
        }
    }

    init() {
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('focus', () => this.handleFocus());
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }

    handleInput(e) {
        const query = e.target.value.trim();
        
        if (this.selectedClient && this.selectedClient.nome !== query) {
            this.clearSelection();
        }
        
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }
        
        this.searchTimeout = setTimeout(() => {
            this.searchClients(query);
        }, 300);
    }

    handleKeydown(e) {
        const suggestions = this.suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.currentFocus = Math.min(this.currentFocus + 1, suggestions.length - 1);
            this.updateFocus(suggestions);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.currentFocus = Math.max(this.currentFocus - 1, -1);
            this.updateFocus(suggestions);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.currentFocus >= 0 && suggestions[this.currentFocus]) {
                this.selectSuggestion(suggestions[this.currentFocus]);
            }
        } else if (e.key === 'Escape') {
            this.hideSuggestions();
        }
    }

    handleFocus() {
        if (this.input.value.length >= 2 && this.suggestionsContainer.children.length > 0) {
            this.showSuggestions();
        }
    }

    handleBlur(e) {
        setTimeout(() => {
            if (!this.suggestionsContainer.contains(document.activeElement)) {
                this.hideSuggestions();
            }
        }, 150);
    }

    async searchClients(query) {
        try {
            const cacheKey = query.toLowerCase();
            if (this.cache.has(cacheKey)) {
                this.displaySuggestions(this.cache.get(cacheKey), query);
                return;
            }

            this.showLoading();
            
            const response = await fetch(`/api/clientes/search?q=${encodeURIComponent(query)}&limit=10`);
            const data = await response.json();
            
            this.hideLoading();
            
            if (data.success) {
                this.cache.set(cacheKey, data.clientes);
                this.displaySuggestions(data.clientes, query);
            } else {
                this.showError(data.message || 'Erro na busca');
            }
            
        } catch (error) {
            this.hideLoading();
            this.showError('Erro de conexão');
            Logger.handleError('Erro na busca de clientes', error);
        }
    }

    displaySuggestions(clients, query) {
        this.suggestionsContainer.innerHTML = '';
        this.currentFocus = -1;
        
        if (clients.length === 0) {
            this.suggestionsContainer.innerHTML = `
                <div class="autocomplete-no-results">
                    Nenhum cliente encontrado para "${query}"
                </div>
            `;
            this.showSuggestions();
            return;
        }
        
        clients.forEach((client, index) => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = 'autocomplete-suggestion';
            suggestionDiv.setAttribute('data-index', index);
            
            const companyInfo = client.empresa ? 
                `<span class="suggestion-company">${client.empresa}</span>` : 
                '<span style="color: #9ca3af;">Empresa não informada</span>';
            
            const phoneInfo = client.whatsapp ? 
                `<span class="suggestion-phone">${Utils.formatPhone(client.whatsapp)}</span>` : 
                '<span style="color: #9ca3af;">Telefone não informado</span>';
            
            suggestionDiv.innerHTML = `
                <div class="suggestion-primary">${this.highlightMatch(client.nome, query)}</div>
                <div class="suggestion-secondary">
                    ${companyInfo}
                    ${phoneInfo}
                </div>
            `;
            
            suggestionDiv.addEventListener('click', () => {
                this.selectClient(client);
            });
            
            this.suggestionsContainer.appendChild(suggestionDiv);
        });
        
        this.showSuggestions();
    }

    selectClient(client) {
        this.selectedClient = client;
        this.input.value = client.nome;
        
        this.fillRelatedFields(client);
        this.showSelectionFeedback();
        this.hideSuggestions();
        
        this.input.dispatchEvent(new CustomEvent('clientSelected', {
            detail: client
        }));
    }

    fillRelatedFields(client) {
        const empresaField = document.getElementById('nome_cliente');
        if (empresaField) {
            const empresaValue = client.empresa || '';
            empresaField.value = empresaValue;
            empresaField.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        const telefoneField = document.getElementById('telefone_cliente');
        if (telefoneField) {
            const telefoneValue = client.whatsapp ? Utils.formatPhone(client.whatsapp) : '';
            telefoneField.value = telefoneValue;
            telefoneField.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    showSelectionFeedback() {
        this.input.classList.add('client-selected');
        setTimeout(() => {
            this.input.classList.remove('client-selected');
        }, 3000);
    }

    clearSelection() {
        this.selectedClient = null;
        const empresaField = document.getElementById('nome_cliente');
        const telefoneField = document.getElementById('telefone_cliente');
        
        if (empresaField) {
            empresaField.value = '';
            empresaField.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        if (telefoneField) {
            telefoneField.value = '';
            telefoneField.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    updateFocus(suggestions) {
        suggestions.forEach((suggestion, index) => {
            suggestion.classList.toggle('active', index === this.currentFocus);
        });
    }

    selectSuggestion(suggestionElement) {
        const index = parseInt(suggestionElement.getAttribute('data-index'));
        const cacheKey = this.input.value.toLowerCase();
        const clients = this.cache.get(cacheKey);
        
        if (clients && clients[index]) {
            this.selectClient(clients[index]);
        }
    }

    showSuggestions() {
        this.suggestionsContainer.style.display = 'block';
        this.input.classList.add('autocomplete-active');
    }

    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
        this.input.classList.remove('autocomplete-active');
        this.currentFocus = -1;
    }

    showLoading() {
        this.input.classList.add('loading');
        this.suggestionsContainer.innerHTML = `
            <div class="autocomplete-loading">
                <i class="fas fa-spinner fa-spin"></i> Buscando clientes...
            </div>
        `;
        this.showSuggestions();
    }

    hideLoading() {
        this.input.classList.remove('loading');
    }

    showError(message) {
        this.suggestionsContainer.innerHTML = `
            <div class="autocomplete-no-results">
                ❌ ${message}
            </div>
        `;
        this.showSuggestions();
    }

    highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    getSelectedClient() {
        return this.selectedClient;
    }

    reloadCache() {
        this.cache.clear();
    }
}

// ================================================
// CLASSE PRINCIPAL - AGENDA EXECUTIVA
// ================================================
class AgendaExecutiva {
    constructor() {
        this.state = {
            meetings: [],
            filteredMeetings: [],
            editingId: null,
            messageTemplate: '',
            monitoringActive: false,
            whatsappConnected: false,
            loading: false,
            submitting: false,
            retryCount: 0,
            lastWeekCheck: null,
            ignoreConflict: false,
            currentConflictModal: null
        };

        this.config = {
            autoRefreshInterval: 60000,
            statusUpdateInterval: 30000,
            debounceDelay: 300,
            maxRetries: 3,
            retryDelay: 2000
        };

        this.intervals = {
            autoRefresh: null,
            statusUpdate: null,
            connectionCheck: null
        };

        this.elements = {};
        this.apiManager = new ApiManager();
        this.modalManager = new ModalManager();
        this.clientAutocomplete = null;
        
        this.bindMethods();
        this.init();
    }

    bindMethods() {
        this.handleFormSubmit = this.handleFormSubmit.bind(this);
        this.handleFilterChange = Utils.debounce(this.applyFilters.bind(this), this.config.debounceDelay);
    }

async init() {
    this.showLoading(true);

    try {
        await this.cacheElements();
        this.setupEventListeners();
        this.addResponsiveButtonStyles();
        this.updateWeekInfo();
        await this.loadInitialData();
        this.applyDefaultFilter();
        this.startAutoRefresh();
        await this.updateWhatsAppStatusIndicator();

        // Inicializa monitoramento com delay leve para evitar sobrecarga
        setTimeout(() => {
            this.initializeMonitoring();
            if (this.monitoringManager && typeof this.monitoringManager.startMonitoring === 'function') {
                this.monitoringManager.startMonitoring().catch(err =>
                    Logger.handleError('Erro ao iniciar monitoramento', err)
                );
            }
        }, 2000); // 2 segundos (reduzido de 3s)

        Logger.log('Sistema inicializado com sucesso', 'success');
    } catch (error) {
        Logger.handleError('Erro na inicialização do sistema', error);
    } finally {
        this.showLoading(false);
    }
}


    async cacheElements() {
        const elementsMap = {
            // Modais
            modal: 'modal',
            whatsappModal: 'whatsappModal',
            messageTemplateModal: 'messageTemplateModal',
            whatsappStatusModal: 'whatsappStatusModal',
            meetingDetailsModal: 'meetingDetailsModal',
            
            // Formulários
            formReuniao: 'formReuniao',
            
            // Grids e containers
            meetingsGrid: 'meetingsGrid',
            meetingDetailsContent: 'meetingDetailsContent',
            
            // Filtros
            searchInput: 'searchInput',
            statusFilter: 'statusFilter',
            dateFilter: 'dateFilter',
            confirmationFilter: 'confirmationFilter',
            
            // Status WhatsApp
            whatsappStatus: 'whatsappStatus',
            statusText: 'statusText',
            connectionIndicator: 'connectionIndicator',
            connectionText: 'connectionText',
            connectionDetails: 'connectionDetails',
            monitoringIndicator: 'monitoringIndicator',
            monitoringText: 'monitoringText',
            monitoredPhones: 'monitoredPhones',
            qrCodeSection: 'qrCodeSection',
            qrCodeDisplay: 'qrCodeDisplay',
            recentActivity: 'recentActivity',
            
            // Outros elementos
            weekText: 'weekText',
            weekInfo: 'weekInfo',
            modalTitle: 'modalTitle',
            submitText: 'submitText'
        };

        Object.entries(elementsMap).forEach(([key, id]) => {
            const element = document.getElementById(id);
            if (element) {
                this.elements[key] = element;
            } else {
                console.warn(`Elemento não encontrado: ${id}`);
            }
        });
    }

    setupEventListeners() {
        if (this.elements.formReuniao) {
            this.elements.formReuniao.addEventListener('submit', this.handleFormSubmit);
        }

        ['searchInput', 'statusFilter', 'dateFilter', 'confirmationFilter'].forEach(filter => {
            if (this.elements[filter]) {
                this.elements[filter].addEventListener('input', this.handleFilterChange);
                this.elements[filter].addEventListener('change', this.handleFilterChange);
            }
        });

        const templateTextarea = document.getElementById('message_template');
        if (templateTextarea) {
            templateTextarea.addEventListener('input', Utils.debounce(() => this.previewTemplate(), 500));
        }

        const meetingSelect = document.getElementById('meeting_select');
        if (meetingSelect) {
            meetingSelect.addEventListener('change', () => this.updateMessageFromMeeting());
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadMeetings(),
            this.loadMessageTemplate(),
            this.checkWhatsAppStatus()
        ]);
    }

    async loadMeetings() {
        try {
            const data = await this.apiManager.request('/agenda/dados');
            
            if (Array.isArray(data)) {
                this.setState({ meetings: data });
                Logger.log(`${data.length} reuniões carregadas`, 'success');
                return data;
            } else if (data.erro) {
                throw new Error(data.erro);
            } else {
                this.setState({ meetings: [] });
                Logger.log('Nenhuma reunião encontrada');
                return [];
            }
        } catch (error) {
            Logger.handleError('Erro ao carregar reuniões', error);
            this.setState({ meetings: [] });
            return [];
        }
    }

    collectFormData() {
        const getFieldValue = (fieldId) => {
            const element = document.getElementById(fieldId);
            if (!element) {
                console.warn(`Campo ${fieldId} não encontrado`);
                return '';
            }
            
            const rawValue = element.value;
            const stringValue = (rawValue || '').toString().trim();
            
            return stringValue;
        };
        
        const getCheckboxValue = (fieldId) => {
            const element = document.getElementById(fieldId);
            return element ? element.checked : false;
        };

        const formData = {
            titulo: getFieldValue('titulo'),
            convidado: getFieldValue('convidado'),
            data_hora: getFieldValue('data_hora'),
            assunto: getFieldValue('assunto'),
            link: getFieldValue('link'),
            nome_cliente: getFieldValue('nome_cliente'),
            telefone_cliente: getFieldValue('telefone_cliente'),
            local_reuniao: getFieldValue('local_reuniao'),
            numero_pessoas: getFieldValue('numero_pessoas'), // 🆕 NOVO
            auto_send_whatsapp: !this.state.editingId ? getCheckboxValue('auto_send_whatsapp') : false
        };
        
        return formData;
    }

    async saveMeetingFromForm() {
        if (this.state.submitting) {
            return false;
        }

        try {
            this.setState({ submitting: true });

            const formData = this.collectFormData();
            const validationErrors = FormValidator.validateMeetingData({
                ...formData,
                editing: !!this.state.editingId
            });
            
            if (validationErrors.length > 0) {
                NotificationManager.show(validationErrors.join('\n'), 'error');
                return false;
            }

            if (!this.state.ignoreConflict) {
                const conflictCheck = await this.checkTimeConflict(formData);
                
                if (conflictCheck.hasConflict) {
                    this.showConflictModal(conflictCheck);
                    return false;
                }
                
                if (conflictCheck.error) {
                    NotificationManager.show('Aviso: ' + conflictCheck.message, 'warning');
                }
            }

            this.setState({ ignoreConflict: false });

            formData._timestamp = Date.now();
            formData._client_id = Math.random().toString(36).substr(2, 9);

            const success = await this.saveMeeting(formData);
            
            if (success) {
                setTimeout(() => this.applyFilters(), 500);
                return true;
            }
            
            return false;
            
        } catch (error) {
            Logger.handleError('Erro ao processar formulário', error);
            return false;
        } finally {
            this.setState({ submitting: false });
        }
    }

    async saveMeeting(meetingData) {
        const url = this.state.editingId ? 
            `/agenda/editar/${this.state.editingId}` : 
            '/agenda/salvar';
        
        const method = this.state.editingId ? 'PUT' : 'POST';

        try {
            const data = await this.apiManager.request(url, {
                method,
                body: JSON.stringify(meetingData)
            });

            if (data) {
                const message = data.mensagem || data.message || 'Reunião salva com sucesso!';
                NotificationManager.show(message, 'success');
                
                if (meetingData.auto_send_whatsapp && !this.state.editingId) {
                    this.processAutoSendResponse(data);
                }
                
                await this.loadMeetings();
                this.modalManager.close('modal');
                this.resetForm();
                return true;
                
            } else {
                throw new Error('Resposta vazia do servidor');
            }
        } catch (error) {
            Logger.handleError('Erro ao salvar reunião', error);
            return false;
        }
    }

    processAutoSendResponse(data) {
        if (data.whatsapp_auto_sent === true || data.auto_send_status === 'success') {
            NotificationManager.show('Mensagem WhatsApp enviada automaticamente!', 'success');
        } else if (data.auto_send_error) {
            NotificationManager.show(`Reunião salva, mas erro no WhatsApp: ${data.auto_send_error}`, 'warning');
        } else if (data.whatsapp_message) {
            NotificationManager.show(`WhatsApp: ${data.whatsapp_message}`, 'info');
        }
    }

    async checkTimeConflict(meetingData) {
        try {
            const payload = {
                data_hora: meetingData.data_hora,
                meeting_id: this.state.editingId || null,
                tolerancia_minutos: 15
            };
            
            const response = await this.apiManager.request('/agenda/verificar-conflito', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            
            if (response.tem_conflito) {
                return {
                    hasConflict: true,
                    conflictInfo: response.conflito,
                    message: response.mensagem,
                    suggestions: response.sugestoes || []
                };
            }
            
            return {
                hasConflict: false,
                message: 'Horário disponível'
            };
            
        } catch (error) {
            Logger.handleError('Erro ao verificar conflito', error);
            return {
                hasConflict: false,
                message: 'Não foi possível verificar conflitos de horário',
                error: true
            };
        }
    }

    showConflictModal(conflictData) {
        const modal = document.createElement('div');
        modal.className = 'modal conflict-modal';
        modal.style.display = 'flex';
        modal.style.zIndex = '10001';
        
        const suggestionsHTML = conflictData.suggestions && conflictData.suggestions.length > 0 
            ? `
                <div class="conflict-suggestions">
                    <h4>Horários alternativos sugeridos:</h4>
                    <div class="suggestions-list">
                        ${conflictData.suggestions.map(suggestion => `
                            <button class="suggestion-btn" 
                                    onclick="agenda.applySuggestion('${suggestion.data_hora}', '${suggestion.data_formatada}', '${suggestion.hora_formatada}')">
                                ${suggestion.data_formatada} às ${suggestion.hora_formatada}
                                <small>(${suggestion.diferenca_original})</small>
                            </button>
                        `).join('')}
                    </div>
                </div>
            `
            : '<p><em>Nenhuma sugestão automática disponível.</em></p>';
        
        modal.innerHTML = `
            <div class="modal-content conflict-content">
                <div class="modal-header conflict-header">
                    <h2>Conflito de Horário Detectado</h2>
                    <button class="close-btn" onclick="agenda.closeConflictModal()">&times;</button>
                </div>
                
                <div class="modal-body">
                    <div class="conflict-info">
                        <h3>Reunião em conflito:</h3>
                        <div class="conflict-details">
                            <p><strong>Título:</strong> ${conflictData.conflictInfo.titulo}</p>
                            <p><strong>Convidado:</strong> ${conflictData.conflictInfo.convidado}</p>
                            <p><strong>Horário:</strong> ${new Date(conflictData.conflictInfo.data_hora).toLocaleString('pt-BR')}</p>
                            ${conflictData.conflictInfo.nome_cliente ? `<p><strong>Cliente:</strong> ${conflictData.conflictInfo.nome_cliente}</p>` : ''}
                            <p><strong>Diferença:</strong> ${conflictData.conflictInfo.diferenca_minutos} minutos</p>
                        </div>
                    </div>
                    
                    ${suggestionsHTML}
                    
                    <div class="conflict-actions">
                        <button class="btn btn-danger" onclick="agenda.forceCreateMeeting()">
                            Criar Mesmo Assim
                        </button>
                        <button class="btn btn-secondary" onclick="agenda.closeConflictModal()">
                            Cancelar
                        </button>
                        <button class="btn btn-primary" onclick="agenda.editDateTime()">
                            Alterar Horário
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.state.currentConflictModal = modal;
        this.addConflictModalStyles();
    }

    addConflictModalStyles() {
        if (!document.getElementById('conflict-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'conflict-modal-styles';
            style.textContent = `
                .conflict-modal {
                    background-color: rgba(0, 0, 0, 0.7);
                    backdrop-filter: blur(4px);
                }
                
                .conflict-content {
                    max-width: 600px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                }
                
                .conflict-header {
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white;
                    padding: 20px;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .conflict-actions {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                    margin-top: 20px;
                    flex-wrap: wrap;
                }
                
                .conflict-actions .btn {
                    padding: 10px 16px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.2s;
                    min-width: 120px;
                }
            `;
            document.head.appendChild(style);
        }
    }
    async addToMonitoring(meetingId, phone) {
        try {
            const cleanPhone = phone.replace(/\D/g, '');
            const result = await this.apiManager.request('/whatsapp/add-to-monitoring', {
                method: 'POST',
                body: JSON.stringify({
                    meeting_id: parseInt(meetingId),
                    phone: cleanPhone
                })
            });
            
            if (result.success) {
                Logger.log(`Telefone ${cleanPhone} monitorado (reunião ${meetingId})`, 'success');
                return true;
            }
            return false;
        } catch (error) {
            Logger.log(`Erro ao adicionar monitoramento: ${error.message}`, 'warn');
            return false;
        }
    }

    closeConflictModal() {
        if (this.state.currentConflictModal) {
            document.body.removeChild(this.state.currentConflictModal);
            this.state.currentConflictModal = null;
        }
    }

    applySuggestion(dataHora, dataFormatada, horaFormatada) {
        const dataHoraField = document.getElementById('data_hora');
        if (dataHoraField) {
            dataHoraField.value = dataHora;
            NotificationManager.show(`Horário alterado para ${dataFormatada} às ${horaFormatada}`, 'success');
        }
        this.closeConflictModal();
    }

    editDateTime() {
        this.closeConflictModal();
        const dataHoraField = document.getElementById('data_hora');
        if (dataHoraField) {
            dataHoraField.focus();
            NotificationManager.show('Altere a data/horário da reunião e tente novamente', 'info');
        }
    }

    forceCreateMeeting() {
        this.closeConflictModal();
        this.setState({ ignoreConflict: true });
        this.saveMeetingFromForm();
    }

    // ================================================
    // WHATSAPP MANAGEMENT
    // ================================================

    async checkWhatsAppStatus() {
        try {
            const data = await this.apiManager.request('/whatsapp/status');
            this.updateConnectionStatus(data);
            await this.updateMonitoringStatus();
            return data;
        } catch (error) {
            Logger.handleError('Erro ao verificar status do WhatsApp', error);
            this.updateConnectionStatus({
                connected: false,
                status_message: 'Erro de conexão',
                instance_active: false,
                monitoring_active: false
            });
            return null;
        }
    }

    updateConnectionStatus(data) {
        const isConnected = data.connected === true;
        this.setState({ whatsappConnected: isConnected });

        const elements = {
            indicator: this.elements.connectionIndicator,
            text: this.elements.connectionText,
            details: this.elements.connectionDetails,
            statusIndicator: this.elements.whatsappStatus,
            statusText: this.elements.statusText
        };

        if (isConnected) {
            if (elements.indicator) {
                elements.indicator.classList.add('connected');
                elements.indicator.classList.remove('disconnected');
            }
            if (elements.text) elements.text.textContent = 'Conectado';
            if (elements.details) elements.details.textContent = data.status_message || 'WhatsApp Web conectado';
            if (elements.statusIndicator) elements.statusIndicator.className = 'whatsapp-status-indicator connected';
            if (elements.statusText) elements.statusText.textContent = 'Conectado';
            this.hideQRSection();
        } else {
            if (elements.indicator) {
                elements.indicator.classList.add('disconnected');
                elements.indicator.classList.remove('connected');
            }
            if (elements.text) elements.text.textContent = 'Desconectado';
            if (elements.details) elements.details.textContent = data.status_message || 'WhatsApp Web não conectado';
            if (elements.statusIndicator) elements.statusIndicator.className = 'whatsapp-status-indicator disconnected';
            if (elements.statusText) elements.statusText.textContent = 'Desconectado';
            
            if (data.status_message?.toLowerCase().includes('qr') || 
                data.status_message?.toLowerCase().includes('aguardando')) {
                this.showQRSection();
            }
        }
    }

    async updateMonitoringStatus() {
        try {
            const response = await fetch('/api/status-changes/check');
            if (!response.ok) {
                if (response.status === 404) {
                    // Endpoint não existe - silenciar erro
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            // Silenciar erros de rede para não poluir console
            return null;
        }
    }

    async checkMonitoringHealth() {
        try {
            const response = await fetch('/api/monitoring/health');
            if (!response.ok) {
                if (response.status === 404) {
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            return null;
        }
    }


    updateMonitoringUI(isActive, phoneCount, statusMessage) {
        if (this.elements.monitoringIndicator) {
            this.elements.monitoringIndicator.className = isActive ? 'monitoring-active' : 'monitoring-inactive';
        }
        
        if (this.elements.monitoringText) {
            this.elements.monitoringText.textContent = statusMessage;
        }
        
        if (this.elements.monitoredPhones) {
            this.elements.monitoredPhones.textContent = phoneCount > 0 ? `${phoneCount} telefones` : 'Nenhum telefone';
        }
    }

    async loadMessageTemplate() {
        try {
            const data = await this.apiManager.request('/whatsapp/template');
            if (data.success && data.template) {
                this.setState({ messageTemplate: data.template });
                Logger.log('Template de mensagem carregado', 'success');
            }
        } catch (error) {
            Logger.handleError('Erro ao carregar template de mensagem', error);
        }
    }

    collectWhatsAppFormData() {
        return {
            phoneNumber: document.getElementById('whatsapp_number')?.value.trim() || '',
            meetingId: document.getElementById('meeting_select')?.value || '',
            message: document.getElementById('whatsapp_message')?.value.trim() || '',
            sendType: document.querySelector('input[name="send_type"]:checked')?.value || 'whatsapp_web'
        };
    }

    async sendWhatsApp() {
        const formData = this.collectWhatsAppFormData();
        const validationErrors = FormValidator.validateWhatsAppData(formData);
        
        if (validationErrors.length > 0) {
            NotificationManager.show(validationErrors.join('\n'), 'error');
            return;
        }

        if (!this.state.whatsappConnected) {
            NotificationManager.show('WhatsApp não está conectado. Conecte primeiro para enviar mensagens.', 'error');
            return;
        }

        const cleanPhone = formData.phoneNumber.replace(/\D/g, '');

        if (formData.sendType === 'whatsapp_web') {
            await this.sendViaWhatsAppWeb(formData.meetingId, cleanPhone, formData.message);
        } else {
            this.sendViaDirect(cleanPhone, formData.message);
        }
    }

    async sendViaWhatsAppWeb(meetingId, phone, message) {
        const btn = document.querySelector('.btn-whatsapp-send');
        if (!btn) return;

        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        btn.disabled = true;

        try {
            let endpoint, payload;
            let actualMeetingId = null;
            
            if (meetingId && meetingId !== '') {
                endpoint = '/whatsapp/send-formatted-message';
                payload = { meeting_id: parseInt(meetingId) };
                actualMeetingId = parseInt(meetingId);
            } else {
                endpoint = '/whatsapp/send-message';
                payload = { 
                    phone: phone,
                    message: message,
                    meeting_id: null
                };
            }

            const data = await this.apiManager.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (data.success) {
                NotificationManager.show('Mensagem enviada! Monitorando respostas...', 'success');
                this.modalManager.close('whatsappModal');
                
                // CORREÇÃO: Adiciona ao monitoramento imediatamente
                if (actualMeetingId) {
                    const meeting = this.state.meetings.find(m => m.id === actualMeetingId);
                    if (meeting && meeting.phone) {
                        await this.addToMonitoring(actualMeetingId, meeting.phone);
                    }
                }
                
                // Força atualização imediata
                setTimeout(async () => {
                    await this.loadMeetings();
                    this.applyFilters();
                    if (this.monitoringManager) {
                        await this.monitoringManager.forceUpdate();
                    }
                }, 2000);
                
            } else {
                throw new Error(data.message || 'Erro ao enviar mensagem');
            }
        } catch (error) {
            Logger.handleError('Erro ao enviar via WhatsApp Web', error);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    sendViaDirect(phone, message) {
        const encodedMessage = encodeURIComponent(message);
        const whatsappUrl = `https://wa.me/${phone}?text=${encodedMessage}`;
        
        window.open(whatsappUrl, '_blank', 'noopener,noreferrer');
        this.modalManager.close('whatsappModal');
    }

    formatMessageTemplate(template, meetingData) {
        try {
            const dataHora = new Date(meetingData.datetime);
            if (isNaN(dataHora.getTime())) {
                throw new Error('Data/hora inválida');
            }

            const dataFormatada = dataHora.toLocaleDateString('pt-BR');
            const horaFormatada = dataHora.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit'
            });

            let linkReuniao = "";
            if (meetingData.link && meetingData.link.trim()) {
                linkReuniao = `Link da Reunião: ${meetingData.link}`;
            }

            const replacements = {
                '{nome_convidado}': meetingData.convidado || '',
                '{data_reuniao}': dataFormatada,
                '{hora_reuniao}': horaFormatada,
                '{assunto}': Utils.ensureString(meetingData.assunto) || '',
                '{nome_cliente}': meetingData.client || '',
                '{local_reuniao}': meetingData.local || 'A definir',
                '{link_reuniao}': linkReuniao,
                '{telefone_cliente}': meetingData.phone || ''
            };

            let formattedMessage = template;

            Object.entries(replacements).forEach(([placeholder, value]) => {
                const escapedPlaceholder = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp(escapedPlaceholder, 'g');
                formattedMessage = formattedMessage.replace(regex, value || '');
            });

            return formattedMessage;

        } catch (error) {
            Logger.handleError('Erro ao formatar template', error);
            return template;
        }
    }
// ...existing code...

    loadDefaultMessage() {
        if (!this.state.messageTemplate) {
            NotificationManager.show('Template não carregado. Carregando...', 'info');
            this.loadMessageTemplate().then(() => {
                setTimeout(() => this.loadDefaultMessage(), 500);
            });
            return;
        }

        const meetingSelect = document.getElementById('meeting_select');
        const messageField = document.getElementById('whatsapp_message');
        
        if (!meetingSelect || !messageField) return;

        const meetingId = meetingSelect.value;
        
        if (meetingId) {
            const selectedMeeting = this.state.meetings.find(m => m.id == meetingId);
            if (selectedMeeting) {
                const formattedMessage = this.formatMessageTemplate(this.state.messageTemplate, selectedMeeting);
                messageField.value = formattedMessage;
            }
        } else {
            messageField.value = this.state.messageTemplate;
        }
    }

    updateMessageFromMeeting() {
        const meetingSelect = document.getElementById('meeting_select');
        const phoneField = document.getElementById('whatsapp_number');
        const messageField = document.getElementById('whatsapp_message');
        
        if (!meetingSelect || !this.state.messageTemplate) return;

        const meetingId = meetingSelect.value;
        
        if (meetingId) {
            const selectedMeeting = this.state.meetings.find(m => m.id == meetingId);
            if (selectedMeeting) {
                const formattedMessage = this.formatMessageTemplate(this.state.messageTemplate, selectedMeeting);
                if (messageField) messageField.value = formattedMessage;
                
                if (selectedMeeting.phone && phoneField) {
                    phoneField.value = selectedMeeting.phone.replace(/\D/g, '');
                }
            }
        } else {
            if (messageField) messageField.value = this.state.messageTemplate;
            if (phoneField) phoneField.value = '';
        }
    }

    async generateQRCode() {
        if (!this.elements.qrCodeDisplay) return;

        this.elements.qrCodeDisplay.innerHTML = `
            <div class="qr-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Gerando QR Code...</p>
            </div>
        `;
        
        this.showQRSection();

        try {
            const data = await this.apiManager.request('/whatsapp/generate-qr', { method: 'POST' });
            
            if (data.success && data.qr_code) {
                this.elements.qrCodeDisplay.innerHTML = `
                    <div class="qr-code-container">
                        <img src="data:image/png;base64,${data.qr_code}" 
                             alt="QR Code WhatsApp" 
                             style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px;">
                        <p style="margin-top: 10px; font-size: 14px; color: #666;">
                            Escaneie este código com seu WhatsApp para conectar
                        </p>
                    </div>
                `;
            } else {
                throw new Error(data.message || 'Erro ao gerar QR Code');
            }
        } catch (error) {
            Logger.handleError('Erro ao gerar QR Code', error);
            this.elements.qrCodeDisplay.innerHTML = `
                <div class="qr-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Erro ao gerar QR Code: ${error.message}</p>
                    <button onclick="agenda.generateQRCode()" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Tentar Novamente
                    </button>
                </div>
            `;
        }
    }

    async restartWhatsApp() {
        const btn = event?.target;
        if (!btn) return;

        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reiniciando...';
        btn.disabled = true;

        try {
            const data = await this.apiManager.request('/whatsapp/restart', { method: 'POST' });
            
            if (data.success) {
                NotificationManager.show('WhatsApp reiniciado com sucesso!', 'success');
                
                setTimeout(async () => {
                    await this.checkWhatsAppStatus();
                    this.generateQRCode();
                }, 2000);
            } else {
                throw new Error(data.message || 'Erro ao reiniciar');
            }
        } catch (error) {
            Logger.handleError('Erro ao reiniciar WhatsApp', error);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    async toggleMonitoring() {
        const isActive = this.state.monitoringActive;
        const endpoint = isActive ? '/whatsapp/stop-monitoring' : '/whatsapp/debug-monitoring';
        
        const btn = event?.target;
        if (!btn) return;

        const originalText = btn.innerHTML;
        
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
        btn.disabled = true;

        try {
            if (isActive) {
                const data = await this.apiManager.request('/whatsapp/stop-monitoring', { method: 'POST' });
                
                if (data.success) {
                    NotificationManager.show('Monitoramento parado com sucesso!', 'success');
                } else {
                    throw new Error(data.message || 'Erro ao parar monitoramento');
                }
            } else {
                const data = await this.apiManager.request('/whatsapp/debug-monitoring');
                
                if (data.success) {
                    NotificationManager.show(
                        'Monitoramento é automático quando mensagens são enviadas. Status atual visualizado!', 
                        'info'
                    );
                } else {
                    throw new Error('Erro ao verificar monitoramento');
                }
            }
            
            await this.updateMonitoringStatus();
        } catch (error) {
            Logger.handleError('Erro ao alterar monitoramento', error);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }



// ================================================
// MODAL FUNCTIONS
// ================================================

// ================================================
// MODAL FUNCTIONS - VERSÃO CORRIGIDA
// ================================================

openModal() {
    this.modalManager.open('modal', () => {
        document.getElementById('titulo')?.focus();
        
        if (!this.clientAutocomplete) {
            this.initializeClientAutocomplete();
        }
    });
}

openWhatsAppModal() {
    this.populateMeetingSelect();
    this.loadMessageTemplate();
    this.modalManager.open('whatsappModal', () => {
        document.getElementById('whatsapp_number')?.focus();
    });
}

openMessageTemplateModal() {
    this.loadCurrentTemplate();
    this.modalManager.open('messageTemplateModal');
}

openWhatsAppStatusModal() {
    this.modalManager.open('whatsappStatusModal');
    this.checkWhatsAppStatus();
    this.loadRecentActivity();
}

closeModal(modalType = 'modal') {
    this.modalManager.close(modalType);
    
    if (modalType === 'modal') {
        this.resetForm();
        this.setState({ editingId: null });
    }
    
    // NOVO: Limpa tracking do modal de detalhes
    if (modalType === 'meetingDetailsModal') {
        this.activeModalMeetingId = null;
    }
}



resetForm() {
    if (this.elements.formReuniao) {
        this.elements.formReuniao.reset();
    }
    
    if (this.elements.modalTitle) this.elements.modalTitle.textContent = 'Nova Reunião';
    if (this.elements.submitText) this.elements.submitText.textContent = 'Salvar Reunião';
    
    const autoSendCheckbox = document.getElementById('auto_send_whatsapp');
    if (autoSendCheckbox) autoSendCheckbox.checked = true;
}

async openMeetingDetailsModal(meetingId) {
    console.log('=== ABERTURA MODAL DETALHES ===');
    console.log('ID recebido:', meetingId);
    
    try {
        const numericId = parseInt(meetingId);
        
        let meeting = this.state.meetings.find(m => 
            m.id === numericId || 
            m.id == meetingId ||
            String(m.id) === String(meetingId)
        );
        
        if (!meeting) {
            console.error('Reunião não encontrada:', meetingId);
            NotificationManager.show('Reunião não encontrada', 'error');
            return false;
        }
        
        // CRUCIAL: Registra qual reunião está no modal
        this.activeModalMeetingId = numericId;
        
        this.modalManager.open('meetingDetailsModal');
        
        if (this.elements.meetingDetailsContent) {
            this.elements.meetingDetailsContent.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 2em; color: #667eea;"></i>
                    <p style="margin-top: 15px;">Carregando detalhes...</p>
                </div>
            `;
        }
        
        let responses = [];
        try {
            const responsesData = await this.apiManager.request(`/agenda/responses/${meeting.id}`);
            if (responsesData && responsesData.success) {
                responses = responsesData.responses || [];
            }
        } catch (err) {
            console.warn('Não foi possível carregar respostas:', err.message);
        }
        
        this.renderMeetingDetails(meeting, responses);
        return true;
        
    } catch (error) {
        console.error('Erro crítico:', error);
        this.activeModalMeetingId = null; // Limpa em caso de erro
        return false;
    }
}

// Função auxiliar de fallback
generateBasicMeetingDetailsHTML(meeting) {
    const dateTimeFormatted = Utils.formatDateTime(meeting.datetime);
    
    return `
        <div class="basic-meeting-details" style="background: #f9fafb; padding: 15px; border-radius: 8px;">
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Título:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.title || 'Sem título')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Convidado:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.convidado || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Data/Hora:</label>
                <span style="margin-left: 10px; color: #6b7280;">${dateTimeFormatted.full || dateTimeFormatted.original || 'Data inválida'}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Assunto:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(Utils.ensureString(meeting.assunto) || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Cliente:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.client || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Telefone:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.phone || 'Não informado')}</span>
            </div>
            
            <!-- 🆕 ADICIONE ESTE BLOCO -->
            ${meeting.numero_pessoas ? `
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Número de Pessoas:</label>
                <span style="margin-left: 10px; color: #6b7280;">
                    <i class="fas fa-users" style="color: #3b82f6; margin-right: 5px;"></i>
                    ${meeting.numero_pessoas} pessoa${meeting.numero_pessoas > 1 ? 's' : ''}
                </span>
            </div>
            ` : ''}
            <!-- FIM DO NOVO BLOCO -->
            
            <div class="detail-item">
                <label style="font-weight: 600; color: #374151;">Status:</label>
                <span class="confirmation-status status-${meeting.status_confirmacao || 'pending'}" style="margin-left: 10px;">
                    ${this.getConfirmationStatusText(meeting.status_confirmacao || 'pending')}
                </span>
            </div>
        </div>
    `;
}

// ================================================
// FUNÇÃO AUXILIAR: Detalhes Básicos (Fallback)
// ================================================
generateBasicMeetingDetailsHTML(meeting) {
    const dateTimeFormatted = Utils.formatDateTime(meeting.datetime);
    
    return `
        <div class="basic-meeting-details" style="background: #f9fafb; padding: 15px; border-radius: 8px;">
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Título:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.title || 'Sem título')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Convidado:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.convidado || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Data/Hora:</label>
                <span style="margin-left: 10px; color: #6b7280;">${dateTimeFormatted.full || dateTimeFormatted.original || 'Data inválida'}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Assunto:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(Utils.ensureString(meeting.assunto) || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Cliente:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.client || 'Não informado')}</span>
            </div>
            <div class="detail-item" style="margin-bottom: 10px;">
                <label style="font-weight: 600; color: #374151;">Telefone:</label>
                <span style="margin-left: 10px; color: #6b7280;">${Utils.sanitizeInput(meeting.phone || 'Não informado')}</span>
            </div>
            <div class="detail-item">
                <label style="font-weight: 600; color: #374151;">Status:</label>
                <span class="confirmation-status status-${meeting.status_confirmacao || 'pending'}" style="margin-left: 10px;">
                    ${this.getConfirmationStatusText(meeting.status_confirmacao || 'pending')}
                </span>
            </div>
        </div>
    `;
}
    renderMeetingDetails(meeting, responses) {
        if (!this.elements.meetingDetailsContent) return;

        const responsesHTML = responses.length > 0 ? 
            responses.map(response => this.generateResponseHTML(response)).join('') :
            '<div class="no-responses">Nenhuma resposta recebida ainda</div>';

        this.elements.meetingDetailsContent.innerHTML = `
            <div class="meeting-details-section">
                <h3><i class="fas fa-calendar"></i> Informações da Reunião</h3>
                <div class="details-grid">
                    ${this.generateMeetingDetailsHTML(meeting)}
                </div>
            </div>

            <div class="meeting-details-section">
                <h3><i class="fas fa-comments"></i> Respostas do Cliente (${responses.length})</h3>
                <div class="responses-container">
                    ${responsesHTML}
                </div>
            </div>

            <div class="meeting-details-section">
                <h3><i class="fas fa-cog"></i> Ações</h3>
                <div class="action-buttons">
                    ${this.generateActionButtonsHTML(meeting.id)}
                </div>
            </div>
        `;
    }

    generateResponseHTML(response) {
        return `
            <div class="response-item status-${response.status}">
                <div class="response-header">
                    <span class="response-status">${this.getConfirmationStatusText(response.status)}</span>
                    <span class="response-time">${new Date(response.received_at).toLocaleString('pt-BR')}</span>
                    <span class="response-confidence">Confiança: ${Math.round(response.confidence * 100)}%</span>
                </div>
                <div class="response-text">${Utils.sanitizeInput(response.response_text)}</div>
                ${response.analysis_data ? `
                    <div class="response-analysis">
                        <small>Análise: ${this.formatAnalysisData(response.analysis_data)}</small>
                    </div>
                ` : ''}
            </div>
        `;
    }
    formatAnalysisData(analysisData) {
        try {
            let data;
            
            // Se já é um objeto, usa diretamente
            if (typeof analysisData === 'object' && analysisData !== null) {
                data = analysisData;
            } 
            // Se é string, tenta fazer parse
            else if (typeof analysisData === 'string') {
                data = JSON.parse(analysisData);
            } 
            // Fallback
            else {
                return String(analysisData);
            }
            
            return JSON.stringify(data, null, 2);
        } catch (error) {
            Logger.log(`Erro ao formatar análise: ${error.message}`, 'warn');
            return String(analysisData);
        }
    }

    generateMeetingDetailsHTML(meeting) {
        const dateTimeFormatted = Utils.formatDateTime(meeting.datetime);
        
        const details = [
            { label: 'Título:', value: meeting.title },
            { label: 'Convidado:', value: meeting.convidado || 'Não informado' },
            { label: 'Data/Hora:', value: dateTimeFormatted.full || dateTimeFormatted.original },
            { label: 'Assunto:', value: Utils.ensureString(meeting.assunto) || 'Não informado' },
            { label: 'Cliente:', value: meeting.client || 'Não informado' },
            { label: 'Telefone:', value: meeting.phone || 'Não informado' },
            { label: 'Local:', value: meeting.local || 'Não informado' },
            // 🆕 ADICIONE ESTA LINHA
            { label: 'Número de Pessoas:', value: meeting.numero_pessoas ? `${meeting.numero_pessoas} pessoa${meeting.numero_pessoas > 1 ? 's' : ''}` : 'Não informado' }
        ];

        let html = details.map(detail => `
            <div class="detail-item">
                <label>${detail.label}</label>
                <span>${Utils.sanitizeInput(detail.value)}</span>
            </div>
        `).join('');

        if (meeting.link) {
            html += `
                <div class="detail-item">
                    <label>Link:</label>
                    <span><a href="${meeting.link}" target="_blank" rel="noopener noreferrer">${meeting.link}</a></span>
                </div>
            `;
        }

        html += `
            <div class="detail-item">
                <label>Status de Confirmação:</label>
                <span class="confirmation-status status-${meeting.status_confirmacao || 'pending'}">
                    ${this.getConfirmationStatusText(meeting.status_confirmacao || 'pending')}
                </span>
            </div>
        `;

        return html;
    }

    generateActionButtonsHTML(meetingId) {
        return `
            <button class="btn-action btn-confirm" onclick="agenda.setMeetingConfirmation(${meetingId}, 'confirmed')">
                <i class="fas fa-check"></i> Marcar como Confirmada
            </button>
            <button class="btn-action btn-decline" onclick="agenda.setMeetingConfirmation(${meetingId}, 'declined')">
                <i class="fas fa-times"></i> Marcar como Recusada
            </button>
            <button class="btn-action btn-pending" onclick="agenda.setMeetingConfirmation(${meetingId}, 'pending')">
                <i class="fas fa-clock"></i> Marcar como Pendente
            </button>
            <button class="btn-action btn-whatsapp-action" onclick="agenda.sendQuickWhatsApp(${meetingId})">
                <i class="fab fa-whatsapp"></i> Enviar WhatsApp
            </button>
        `;
    }

    async setMeetingConfirmation(meetingId, status) {
    const statusText = this.getConfirmationStatusText(status);
    
    if (!confirm(`Tem certeza que deseja marcar esta reunião como "${statusText}"?`)) {
        return;
    }

    // Mostra loading no modal
    if (this.elements.meetingDetailsContent) {
        this.elements.meetingDetailsContent.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-spinner fa-spin" style="font-size: 2em; color: #667eea;"></i>
                <p style="margin-top: 15px;">Atualizando status...</p>
            </div>
        `;
    }

    try {
        // 1. Atualiza o status via API
        const updateData = await this.apiManager.request(`/agenda/manual-confirmation/${meetingId}`, {
            method: 'POST',
            body: JSON.stringify({ status: status })
        });

        if (!updateData.success) {
            throw new Error(updateData.message || 'Erro ao atualizar status');
        }

        // 2. Busca dados atualizados da reunião específica
        const meetingData = await this.apiManager.request(`/agenda/meeting/${meetingId}`);
        
        if (!meetingData.success) {
            throw new Error('Erro ao buscar dados atualizados da reunião');
        }

        // 3. Atualiza o estado local
        const meetingIndex = this.state.meetings.findIndex(m => m.id === meetingId);
        if (meetingIndex !== -1) {
            this.state.meetings[meetingIndex] = meetingData.meeting;
        }

        // 4. Busca respostas atualizadas
        let responses = [];
        try {
            const responsesData = await this.apiManager.request(`/agenda/responses/${meetingId}`);
            responses = responsesData?.success ? (responsesData.responses || []) : [];
        } catch (err) {
            console.warn('Erro ao carregar respostas:', err);
        }

        // 5. Re-renderiza o modal com dados atualizados
        this.renderMeetingDetails(meetingData.meeting, responses);

        // 6. Destaca visualmente a mudança
        setTimeout(() => {
            const statusElement = document.querySelector('.confirmation-status');
            if (statusElement) {
                statusElement.style.background = '#dcfce7';
                statusElement.style.border = '2px solid #10b981';
                statusElement.style.animation = 'pulse 1s ease-in-out';
                
                setTimeout(() => {
                    statusElement.style.background = '';
                    statusElement.style.border = '';
                    statusElement.style.animation = '';
                }, 2000);
            }
        }, 100);

        // 7. Atualiza lista principal
        this.applyFilters();
        
        NotificationManager.show(`Status atualizado para: ${statusText}`, 'success');

    } catch (error) {
        Logger.handleError('Erro ao atualizar status', error);
        this.modalManager.close('meetingDetailsModal');
    }
}
    // ================================================
    // TEMPLATE MANAGEMENT
    // ================================================

    async saveMessageTemplate() {
        const templateField = document.getElementById('message_template');
        if (!templateField) return;

        const template = templateField.value.trim();
        
        if (!template) {
            NotificationManager.show('Por favor, digite um template válido.', 'error');
            return;
        }

        const requiredPlaceholders = ['{nome_convidado}', '{data_reuniao}', '{hora_reuniao}'];
        const missingPlaceholders = requiredPlaceholders.filter(p => !template.includes(p));
        
        if (missingPlaceholders.length > 0) {
            NotificationManager.show(`Template deve conter os placeholders obrigatórios: ${missingPlaceholders.join(', ')}`, 'error');
            return;
        }

        try {
            const data = await this.apiManager.request('/whatsapp/template', {
                method: 'POST',
                body: JSON.stringify({ template: template })
            });

            if (data.success) {
                NotificationManager.show('Template salvo com sucesso!', 'success');
                this.setState({ messageTemplate: template });
                this.modalManager.close('messageTemplateModal');
            } else {
                throw new Error(data.message || 'Erro ao salvar template');
            }
        } catch (error) {
            Logger.handleError('Erro ao salvar template', error);
        }
    }

    async loadCurrentTemplate() {
        try {
            const data = await this.apiManager.request('/whatsapp/template');
            if (data.success) {
                const templateField = document.getElementById('message_template');
                if (templateField) {
                    templateField.value = data.template;
                    this.previewTemplate();
                }
            }
        } catch (error) {
            Logger.handleError('Erro ao carregar template atual', error);
        }
    }

    previewTemplate() {
        const templateField = document.getElementById('message_template');
        const previewDiv = document.getElementById('messagePreview');

        if (!templateField || !previewDiv) return;

        const template = templateField.value;

        const exampleData = {
            nome_convidado: 'João Silva',
            data_reuniao: '15/02/2024',
            hora_reuniao: '14:30',
            assunto: 'Planejamento Estratégico',
            nome_cliente: 'Empresa XYZ Ltda',
            local_reuniao: 'Escritório Central - Sala A',
            link_reuniao: 'Link da Reunião: https://meet.google.com/abc-def-ghi',
            telefone_cliente: '(11) 99999-9999'
        };

        const preview = template.replace(/\{(\w+)\}/g, (match, key) => {
            return exampleData[key] !== undefined ? exampleData[key] : match;
        });

        previewDiv.textContent = preview;
    }

    // ================================================
    // RECENT ACTIVITY
    // ================================================

    async loadRecentActivity() {
        try {
            const data = await this.apiManager.request('/whatsapp/logs');
            
            if (!this.elements.recentActivity) return;

            if (data.success && data.logs && data.logs.length > 0) {
                const activitiesHTML = data.logs.slice(0, 10).map(log => {
                    const statusIcon = log.status === 'success' ? 'check' : 'exclamation-triangle';
                    const statusClass = log.status === 'success' ? 'success' : 'error';
                    
                    return `
                        <div class="activity-item ${statusClass}">
                            <i class="fas fa-${statusIcon}"></i>
                            <div class="activity-content">
                                <div class="activity-title">
                                    ${Utils.sanitizeInput(log.phone || 'N/A')}
                                </div>
                                <div class="activity-time">${new Date(log.sent_at).toLocaleString('pt-BR')}</div>
                                ${log.error_message ? `<div class="activity-error">${Utils.sanitizeInput(log.error_message)}</div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');

                this.elements.recentActivity.innerHTML = activitiesHTML;
            } else {
                this.elements.recentActivity.innerHTML = '<div class="no-activity">Nenhuma atividade recente</div>';
            }
        } catch (error) {
            Logger.handleError('Erro ao carregar atividades recentes', error);
            if (this.elements.recentActivity) {
                this.elements.recentActivity.innerHTML = '<div class="activity-error">Erro ao carregar atividades</div>';
            }
        }
    }

    // ================================================
    // UI RENDERING
    // ================================================

    renderMeetings(meetingsToRender = this.state.meetings) {
        if (!this.elements.meetingsGrid) return;

        if (meetingsToRender.length === 0) {
            this.renderEmptyState();
            return;
        }

        const nextMeetingId = this.getNextMeetingId(meetingsToRender);
        
        const meetingsHTML = meetingsToRender.map(meeting => {
            const status = this.getMeetingStatus(meeting.datetime);
            const confirmationStatus = meeting.status_confirmacao || 'pending';
            const isNextMeeting = meeting.id === nextMeetingId;
            const cardClass = isNextMeeting ? 'meeting-card upcoming-highlight' : 'meeting-card';
            
            return this.generateMeetingCardHTML(meeting, status, confirmationStatus, cardClass);
        }).join('');

        this.elements.meetingsGrid.innerHTML = meetingsHTML;
    }

    generateMeetingCardHTML(meeting, status, confirmationStatus, cardClass) {
        const title = Utils.sanitizeInput(meeting.title || '');
        const convidado = Utils.sanitizeInput(meeting.convidado || '');
        const assunto = Utils.sanitizeInput(Utils.ensureString(meeting.assunto) || '');
        const client = Utils.sanitizeInput(meeting.client || '');
        const phone = Utils.sanitizeInput(meeting.phone || '');
        const local = Utils.sanitizeInput(meeting.local || '');
        const link = meeting.link || '';
        const numeroPessoas = meeting.numero_pessoas; // 🆕 EXTRAI O VALOR

        const dateTimeInfo = Utils.formatDateTime(meeting.datetime);

        return `
            <div class="${cardClass}">
                <div class="meeting-header">
                    <h3 class="meeting-title">${title}</h3>
                    <div class="meeting-badges">
                        <span class="meeting-status status-${status}">${this.getStatusText(status)}</span>
                        <span class="confirmation-status status-${confirmationStatus}">
                            ${this.getConfirmationStatusText(confirmationStatus)}
                        </span>
                    </div>
                </div>
                <div class="meeting-info">
                    <div class="info-item time">
                        <i class="fas fa-calendar-alt"></i>
                        <div class="datetime-with-weekday">
                            <div class="weekday">${dateTimeInfo.weekday}</div>
                            <div class="date-time">${dateTimeInfo.dateOnly}, ${dateTimeInfo.timeOnly}</div>
                        </div>
                    </div>
                    ${assunto ? `
                        <div class="info-item">
                            <i class="fas fa-building"></i>
                            <span>${assunto}</span>
                        </div>` : ''}
                    ${convidado ? `
                        <div class="info-item">
                            <i class="fas fa-user-tie"></i>
                            <span>${convidado}</span>
                        </div>` : ''}
                    ${client ? `
                        <div class="info-item">
                            <i class="fas fa-handshake"></i>
                            <span>${client}</span>
                        </div>` : ''}
                    ${phone ? `
                        <div class="info-item">
                            <i class="fas fa-phone"></i>
                            <span>${phone}</span>
                        </div>` : ''}
                    ${local ? `
                        <div class="info-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${local}</span>
                        </div>` : ''}
                    
                    <!-- 🆕 ADICIONE ESTE BLOCO AQUI -->
                    ${numeroPessoas ? `
                        <div class="info-item">
                            <i class="fas fa-users" style="color: #3b82f6;"></i>
                            <span>${numeroPessoas} ${numeroPessoas == 1 ? 'pessoa' : 'pessoas'}</span>
                        </div>` : ''}
                    <!-- FIM DO NOVO BLOCO -->
                    
                    ${link ? `
                        <div class="info-item link">
                            <i class="fas fa-video"></i>
                            <a href="${link}" target="_blank" rel="noopener noreferrer">Acessar reunião</a>
                        </div>` : (!local ? `
                        <div class="info-item">
                            <i class="fas fa-map-marker-alt" style="color: #6b7280;"></i>
                            <span style="color: #6b7280;">Reunião presencial</span>
                        </div>` : '')}
                </div>
                <div class="meeting-actions">
                    <button class="btn-action btn-details" onclick="agenda.openMeetingDetailsModal(${meeting.id})">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                    <button class="btn-action btn-edit" onclick="agenda.editMeeting(${meeting.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    ${phone ? `
                        <button class="btn-action btn-whatsapp-action" onclick="agenda.sendQuickWhatsApp(${meeting.id})" title="Enviar WhatsApp">
                            <i class="fab fa-whatsapp"></i> WhatsApp
                        </button>
                    ` : ''}
                    <button class="btn-action btn-delete" onclick="agenda.deleteMeeting(${meeting.id}, '${title.replace(/'/g, "\\'")}')">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        `;
    }

    renderEmptyState() {
        const filters = this.getActiveFilters();

        let message = 'Nenhuma reunião encontrada';
        
        if (filters.date) {
            const selectedDate = new Date(filters.date).toLocaleDateString('pt-BR');
            message = `Nenhuma reunião encontrada para ${selectedDate}`;
        } else if (filters.confirmation) {
            message = `Nenhuma reunião ${this.getConfirmationStatusText(filters.confirmation).toLowerCase()} encontrada`;
        } else if (filters.status === 'upcoming') {
            message = 'Nenhuma reunião próxima encontrada';
        } else if (filters.status === 'current_week') {
            message = 'Nenhuma reunião nesta semana';
        } else if (filters.status === 'past') {
            message = 'Nenhuma reunião passada encontrada';
        }
        
        this.elements.meetingsGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar-times"></i>
                <h3>${message}</h3>
                <p>Tente ajustar os filtros ou criar uma nova reunião.</p>
            </div>
        `;
    }

    // ================================================
    // MEETING ACTIONS
    // ================================================

    editMeeting(id) {
        const meeting = this.state.meetings.find(m => m.id === id);
        if (!meeting) {
            NotificationManager.show('Reunião não encontrada', 'error');
            return;
        }
        
        this.populateFormWithMeeting(meeting);
        this.setState({ editingId: id });
        
        if (this.elements.modalTitle) this.elements.modalTitle.textContent = 'Editar Reunião';
        if (this.elements.submitText) this.elements.submitText.textContent = 'Atualizar Reunião';
        
        const autoSendCheckbox = document.getElementById('auto_send_whatsapp');
        if (autoSendCheckbox) autoSendCheckbox.checked = false;
        
        this.openModal();
    }

    populateFormWithMeeting(meeting) {
        const setFieldValue = (fieldId, value) => {
            const field = document.getElementById(fieldId);
            if (!field) {
                console.warn(`Campo ${fieldId} não encontrado`);
                return;
            }
            
            field.value = value || '';
        };
            
        setFieldValue('titulo', meeting.title);
        setFieldValue('convidado', meeting.convidado);
        setFieldValue('data_hora', meeting.datetime);
        setFieldValue('assunto', meeting.assunto);
        setFieldValue('nome_cliente', meeting.client);
        setFieldValue('telefone_cliente', meeting.phone);
        setFieldValue('local_reuniao', meeting.local);
        setFieldValue('link', meeting.link);
        setFieldValue('numero_pessoas', meeting.numero_pessoas); // 🆕 NOVO
    }
    async deleteMeeting(id, title) {
        if (!confirm(`Deseja realmente excluir a reunião "${title}"?\n\nEsta ação não pode ser desfeita.`)) {
            return;
        }

        try {
            const data = await this.apiManager.request(`/agenda/excluir/${id}`, {
                method: 'DELETE'
            });

            if (data.mensagem) {
                NotificationManager.show(data.mensagem, 'success');
                await this.loadMeetings();
                this.applyFilters();
            } else if (data.erro) {
                throw new Error(data.erro);
            }
        } catch (error) {
            Logger.handleError('Erro ao excluir reunião', error);
        }
    }

    sendQuickWhatsApp(meetingId) {
        const meeting = this.state.meetings.find(m => m.id === meetingId);
        if (!meeting) {
            NotificationManager.show('Reunião não encontrada', 'error');
            return;
        }

        if (!meeting.phone) {
            NotificationManager.show('Esta reunião não possui telefone cadastrado', 'error');
            return;
        }

        setTimeout(() => {
            const meetingSelect = document.getElementById('meeting_select');
            const phoneField = document.getElementById('whatsapp_number');
            
            if (meetingSelect) meetingSelect.value = meetingId;
            if (phoneField) phoneField.value = meeting.phone.replace(/\D/g, '');
            
            this.updateMessageFromMeeting();
            this.openWhatsAppModal();
        }, 100);
    }

    populateMeetingSelect() {
        const select = document.getElementById('meeting_select');
        if (!select) return;

        select.innerHTML = '<option value="">Selecione uma reunião...</option>';
        
        const upcomingMeetings = this.state.meetings
            .filter(meeting => new Date(meeting.datetime) > new Date())
            .sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
        
        upcomingMeetings.forEach(meeting => {
            const option = document.createElement('option');
            option.value = meeting.id;
            
            const dateTimeInfo = Utils.formatDateTime(meeting.datetime);
            option.textContent = `${meeting.title} - ${dateTimeInfo.compact}`;
            
            select.appendChild(option);
        });
    }

    // ================================================
    // FILTERS AND SEARCH
    // ================================================

    applyFilters() {
        const filters = this.getActiveFilters();
        
        this.state.filteredMeetings = this.state.meetings.filter(meeting => {
            return this.meetingMatchesFilters(meeting, filters);
        });

        this.state.filteredMeetings.sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
        
        this.renderMeetings(this.state.filteredMeetings);
        this.updateFilterInfo();
        
        Logger.log(`Filtros aplicados: ${this.state.filteredMeetings.length} reuniões encontradas`);
    }

    getActiveFilters() {
        return {
            search: this.elements.searchInput?.value.toLowerCase() || '',
            status: this.elements.statusFilter?.value || '',
            date: this.elements.dateFilter?.value || '',
            confirmation: this.elements.confirmationFilter?.value || ''
        };
    }

    meetingMatchesFilters(meeting, filters) {
        const assuntoString = Utils.ensureString(meeting.assunto);
        
        const matchesSearch = !filters.search || 
            meeting.title?.toLowerCase().includes(filters.search) ||
            meeting.convidado?.toLowerCase().includes(filters.search) ||
            assuntoString?.toLowerCase().includes(filters.search) ||
            meeting.client?.toLowerCase().includes(filters.search) ||
            meeting.local?.toLowerCase().includes(filters.search);

        const matchesConfirmation = !filters.confirmation || 
            (meeting.status_confirmacao || 'pending') === filters.confirmation;

        if (filters.date) {
            const meetingDate = new Date(meeting.datetime);
            const filterDate = new Date(filters.date);
            const matchesDate = meetingDate.toISOString().split('T')[0] === filterDate.toISOString().split('T')[0];
            return matchesSearch && matchesDate && matchesConfirmation;
        }

        let matchesStatus = true;
        if (filters.status) {
            if (filters.status === 'current_week') {
                matchesStatus = this.isInCurrentWeek(meeting.datetime);
            } else {
                matchesStatus = this.getMeetingStatus(meeting.datetime) === filters.status;
            }
        }

        return matchesSearch && matchesStatus && matchesConfirmation;
    }

    isInCurrentWeek(datetime) {
        const now = new Date();
        const meetingDate = new Date(datetime);
        
        const startOfWeek = new Date(now);
        startOfWeek.setDate(now.getDate() - now.getDay());
        startOfWeek.setHours(0, 0, 0, 0);
        
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        endOfWeek.setHours(23, 59, 59, 999);
        
        return meetingDate >= startOfWeek && meetingDate <= endOfWeek;
    }

    applyDefaultFilter() {
        if (this.elements.statusFilter) {
            this.elements.statusFilter.value = 'upcoming';
        }
        this.applyFilters();
    }

    clearAllFilters() {
        if (this.elements.searchInput) this.elements.searchInput.value = '';
        if (this.elements.statusFilter) this.elements.statusFilter.value = 'upcoming';
        if (this.elements.dateFilter) this.elements.dateFilter.value = '';
        if (this.elements.confirmationFilter) this.elements.confirmationFilter.value = '';
        this.applyFilters();
    }

    // ================================================
    // AUTO-REFRESH
    // ================================================

    startAutoRefresh() {
        this.stopAutoRefresh();
        
        Logger.log('Iniciando auto-refresh com monitoramento...', 'info');
        
        // 1. Auto-refresh das reuniões (menos frequente)
        this.intervals.autoRefresh = setInterval(async () => {
            try {
                if (this.hasWeekChanged()) {
                    Logger.log('Nova semana detectada, recarregando reuniões...', 'info');
                    await this.loadMeetings();
                    this.applyFilters();
                    this.updateWeekInfo();
                }
            } catch (error) {
                Logger.handleError('Erro no auto-refresh das reuniões', error);
            }
        }, this.config.autoRefreshInterval);

        // 2. CORRIGIDO: Inicializa e inicia monitoramento
        this.initializeMonitoring();

        // 3. Verificação simples de status do WhatsApp
        this.intervals.statusUpdate = setInterval(async () => {
            try {
                if (this.state.whatsappConnected) {
                    await this.updateWhatsAppStatusIndicator();
                }
            } catch (error) {
                console.debug('WhatsApp status update error:', error.message);
            }   
        
        try {
        // ADICIONE ESTA VERIFICAÇÃO:
        if (this.monitoringManager && this.monitoringManager.isMonitoring) {
            Logger.log('Monitoramento já ativo, pulando inicialização duplicada', 'info');
            return;
        }
        
        this.initializeMonitoring();
        if (this.monitoringManager) {
            this.monitoringManager.startMonitoring();
        }
    } catch (error) {
        Logger.handleError('Erro ao iniciar monitoramento', error);
    }
}, 3000);

        Logger.log('Auto-refresh e monitoramento iniciados', 'success');
    }

    // ADICIONE ESTE MÉTODO À CLASSE AgendaExecutiva:
    initializeMonitoring() {
        if (!this.monitoringManager) {
            this.monitoringManager = new MonitoringManager(this);
            Logger.log('Gerenciador de monitoramento inicializado', 'success');
        }
        
        // IMPORTANTE: Inicia o monitoramento automaticamente
        if (!this.monitoringManager.isMonitoring) {
            this.monitoringManager.startMonitoring();
            Logger.log('Monitoramento de respostas iniciado automaticamente', 'success');
        }
        
        return this.monitoringManager;
    }

    // SUBSTITUA O MÉTODO updateMonitoringStatus EXISTENTE:
    async updateMonitoringStatus() {
        if (!this.monitoringManager) {
            this.initializeMonitoring();
            return;
        }
        
        // Se não está monitorando, inicia automaticamente
        if (!this.monitoringManager.isMonitoring) {
            await this.monitoringManager.startMonitoring();
        }
        
        return this.monitoringManager.getStatus();
    }
    async updateWhatsAppStatusIndicator() {
        try {
            const data = await this.checkWhatsAppStatus();
            return data;
        } catch (error) {
            return null;
        }
    }

    stopAutoRefresh() {
        Object.values(this.intervals).forEach(interval => {
            if (interval) {
                clearInterval(interval);
            }
        });
        
        this.intervals = {
            autoRefresh: null,
            statusUpdate: null,
            connectionCheck: null
        };
    }

    refreshWeeklyView() {
        const refreshBtn = document.querySelector('.btn-refresh');
        
        if (!refreshBtn) {
            Logger.handleError('Botão refresh não encontrado');
            return;
        }

        const originalHTML = refreshBtn.innerHTML;
        
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        refreshBtn.disabled = true;
        
        this.loadMeetings().then(() => {
            this.applyFilters();
            this.updateWeekInfo();
            
            setTimeout(() => {
                refreshBtn.innerHTML = originalHTML;
                refreshBtn.disabled = false;
            }, 1000);
        }).catch(error => {
            Logger.handleError('Erro ao atualizar vista semanal', error);
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
        });
    }

    addResponsiveButtonStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .btn-whatsapp-action {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
            }

            .btn-whatsapp-action:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
            }

            .btn-refresh {
                pointer-events: auto !important;
                cursor: pointer !important;
            }

            .btn-refresh:disabled {
                opacity: 0.7 !important;
                cursor: not-allowed !important;
            }

            .btn-action {
                pointer-events: auto !important;
                cursor: pointer !important;
                user-select: none !important;
            }

            .meeting-actions {
                pointer-events: auto !important;
            }

            .meeting-card {
                pointer-events: auto !important;
            }

            .datetime-with-weekday {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .weekday {
                font-weight: 600;
                color: #4f46e5;
                font-size: 0.85em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .date-time {
                color: #6b7280;
                font-size: 0.9em;
            }

            .meeting-card.status-today .weekday {
                color: #059669;
            }

            .meeting-card.status-upcoming .weekday {
                color: #2563eb;
            }

            .meeting-card.status-past .weekday {
                color: #6b7280;
            }

            @media (max-width: 768px) {
                .datetime-with-weekday {
                    flex-direction: row;
                    align-items: center;
                    gap: 8px;
                }
                
                .weekday::after {
                    content: " -";
                    margin-right: 5px;
                }
                
                .weekday {
                    font-size: 0.8em;
                }
                
                .date-time {
                    font-size: 0.85em;
                }
            }

            @media (max-width: 480px) {
                .datetime-with-weekday {
                    flex-direction: column;
                    gap: 1px;
                }
                
                .weekday::after {
                    content: "";
                }
                
                .weekday {
                    font-size: 0.75em;
                }
                
                .date-time {
                    font-size: 0.8em;
                }
            }

            /* Autocomplete Styles */
            .autocomplete-suggestion {
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
                transition: background-color 0.2s;
            }

            .autocomplete-suggestion:hover,
            .autocomplete-suggestion.active {
                background-color: #f3f4f6;
            }

            .suggestion-primary {
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 4px;
            }

            .suggestion-secondary {
                font-size: 0.875rem;
                color: #6b7280;
                display: flex;
                gap: 16px;
            }

            .autocomplete-loading,
            .autocomplete-no-results {
                padding: 16px;
                text-align: center;
                color: #6b7280;
                font-style: italic;
            }

            .autocomplete-active {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .client-selected {
                border-color: #10b981;
                box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
            }

            .loading {
                background-image: url('data:image/svg+xml;charset=UTF-8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%236b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m16 12-4-4-4 4"></path></svg>');
                background-repeat: no-repeat;
                background-position: right 12px center;
                background-size: 16px;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    // ================================================
    // UTILITY FUNCTIONS
    // ================================================

    showLoading(show = true) {
        this.state.loading = show;
        
        if (this.elements.meetingsGrid) {
            if (show) {
                this.elements.meetingsGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        <h3>Carregando reuniões...</h3>
                        <p>Aguarde um momento.</p>
                    </div>
                `;
            }
        }
    }

    showQRSection() {
        if (this.elements.qrCodeSection) {
            this.elements.qrCodeSection.style.display = 'block';
        }
    }

    hideQRSection() {
        if (this.elements.qrCodeSection) {
            this.elements.qrCodeSection.style.display = 'none';
        }
    }

    updateFilterInfo() {
        const filters = this.getActiveFilters();
        
        if (!this.elements.weekInfo || !this.elements.weekText) return;

        if (filters.date) {
            const selectedDate = new Date(filters.date);
            const formattedDate = selectedDate.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            this.elements.weekText.innerHTML = `<i class="fas fa-calendar-day"></i> Reuniões de ${formattedDate}`;
            this.elements.weekInfo.style.background = 'linear-gradient(135deg, #17a2b8, #138496)';
        } else {
            this.elements.weekText.innerHTML = `<i class="fas fa-calendar-week"></i> ${Utils.getCurrentWeekInfo()}`;
            this.elements.weekInfo.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
    }

    updateWeekInfo() {
        if (this.elements.weekText) {
            this.elements.weekText.textContent = Utils.getCurrentWeekInfo();
        }
    }

    hasWeekChanged() {
        const now = new Date();
        const currentWeek = Utils.getWeekNumber(now);
        
        if (this.state.lastWeekCheck === null) {
            this.setState({ lastWeekCheck: currentWeek });
            return false;
        }
        
        if (currentWeek !== this.state.lastWeekCheck) {
            this.setState({ lastWeekCheck: currentWeek });
            return true;
        }
        
        return false;
    }

    getNextMeetingId(meetings) {
        const now = new Date();
        let nextMeeting = null;
        let shortestTime = Infinity;

        meetings.forEach(meeting => {
            const meetingDate = new Date(meeting.datetime);
            if (meetingDate > now) {
                const timeDiff = meetingDate - now;
                if (timeDiff < shortestTime) {
                    shortestTime = timeDiff;
                    nextMeeting = meeting;
                }
            }
        });

        return nextMeeting?.id || null;
    }

    getMeetingStatus(datetime) {
        const now = new Date();
        const meetingDate = new Date(datetime);
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const meetingDay = new Date(meetingDate.getFullYear(), meetingDate.getMonth(), meetingDate.getDate());
        
        if (meetingDay.getTime() === today.getTime()) return 'today';
        if (meetingDate > now) return 'upcoming';
        return 'past';
    }

    getStatusText(status) {
        const statusMap = {
            today: 'Hoje',
            upcoming: 'Próxima',
            past: 'Finalizada'
        };
        return statusMap[status] || 'Agendada';
    }

    getConfirmationStatusText(status) {
        const statusMap = {
            confirmed: 'Confirmada',
            declined: 'Recusada',
            pending: 'Pendente',
            unclear: 'Não Clara',
            reschedule: 'Reagendar'
        };
        return statusMap[status] || 'Pendente';
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        Logger.log(`Estado atualizado: ${Object.keys(newState).join(', ')}`);
    }

    // ================================================
    // EVENT HANDLERS
    // ================================================

    handleFormSubmit(event) {
        event.preventDefault();
        event.stopPropagation();
        
        if (this.state.loading || this.state.submitting) {
            return false;
        }
        
        this.setState({ loading: true });
        
        this.saveMeetingFromForm().finally(() => {
            this.setState({ loading: false });
        });
        
        return false;
    }

    // ================================================
    // AUTOCOMPLETE INTEGRATION
    // ================================================

    initializeClientAutocomplete() {
        const convidadoInput = document.getElementById('convidado');
        const suggestionsContainer = document.getElementById('convidado-suggestions');
        
        if (convidadoInput && suggestionsContainer) {
            this.clientAutocomplete = new ClientAutocomplete('convidado', 'convidado-suggestions');
            
            convidadoInput.addEventListener('clientSelected', (e) => {
                const client = e.detail;
                Logger.log(`Cliente selecionado: ${client.nome}`, 'success');
                NotificationManager.show(`Cliente "${client.nome}" selecionado!`, 'success');
            });
            
            return true;
        }
        
        return false;
    }

    // ================================================
    // CLEANUP
    // ================================================

    cleanup() {
        this.stopAutoRefresh();
        Logger.log('Sistema finalizado e recursos liberados', 'info');
    }

    // ================================================
    // DEBUG E TESTING
    // ================================================

    async testAutoSend() {
        const testData = {
            titulo: 'Teste Auto-Send',
            convidado: 'João Teste',
            data_hora: '2024-12-31T14:00',
            assunto: 'Teste',
            telefone_cliente: '11999999999',
            auto_send_whatsapp: true,
            _timestamp: Date.now()
        };
        
        try {
            const data = await this.apiManager.request('/agenda/salvar', {
                method: 'POST',
                body: JSON.stringify(testData)
            });
            
            if (data.auto_send_error) {
                Logger.handleError('Erro no auto-send', new Error(data.auto_send_error));
            } else {
                Logger.log('Teste de auto-send concluído', 'success');
            }
            
            return data;
        } catch (error) {
            Logger.handleError('Erro no teste', error);
            return null;
        }
    }

    getSystemStatus() {
        return {
            state: {
                meetings: this.state.meetings.length,
                filteredMeetings: this.state.filteredMeetings.length,
                editingId: this.state.editingId,
                monitoringActive: this.state.monitoringActive,
                whatsappConnected: this.state.whatsappConnected,
                loading: this.state.loading,
                submitting: this.state.submitting
            },
            intervals: {
                autoRefresh: !!this.intervals.autoRefresh,
                statusUpdate: !!this.intervals.statusUpdate,
                connectionCheck: !!this.intervals.connectionCheck
            },
            config: this.config
        };
    }
}

// ================================================
// FUNÇÕES GLOBAIS PARA COMPATIBILIDADE
// ================================================
let agenda;
let clientAutocomplete = null;

// Funções globais principais
function openModal() { agenda?.openModal(); }
function closeModal() { agenda?.closeModal(); }
function openWhatsAppModal() { agenda?.openWhatsAppModal(); }
function closeWhatsAppModal() { agenda?.closeModal('whatsappModal'); }
function openMessageTemplateModal() { agenda?.openMessageTemplateModal(); }
function closeMessageTemplateModal() { agenda?.closeModal('messageTemplateModal'); }
function openWhatsAppStatusModal() { agenda?.openWhatsAppStatusModal(); }
function closeWhatsAppStatusModal() { agenda?.closeModal('whatsappStatusModal'); }
function closeMeetingDetailsModal() { agenda?.closeModal('meetingDetailsModal'); }
function salvarReuniao() { agenda?.saveMeetingFromForm(); }
function editMeeting(id) { agenda?.editMeeting(id); }
function deleteMeeting(id, title) { agenda?.deleteMeeting(id, title); }
function applyFilters() { agenda?.applyFilters(); }
function clearAllFilters() { agenda?.clearAllFilters(); }
function refreshWeeklyView() { agenda?.refreshWeeklyView(); }
function sendWhatsApp() { agenda?.sendWhatsApp(); }
function loadDefaultMessage() { agenda?.loadDefaultMessage(); }
function updateMessageFromMeeting() { agenda?.updateMessageFromMeeting(); }
function saveMessageTemplate() { agenda?.saveMessageTemplate(); }
function previewTemplate() { agenda?.previewTemplate(); }
function setMeetingConfirmation(meetingId, status) { agenda?.setMeetingConfirmation(meetingId, status); }
function sendQuickWhatsApp(meetingId) { agenda?.sendQuickWhatsApp(meetingId); }
function generateQRCode() { agenda?.generateQRCode(); }
function restartWhatsApp() { agenda?.restartWhatsApp(); }
function toggleMonitoring() { agenda?.toggleMonitoring(); }

// Funções de autocomplete
async function reloadClientCache() {
    try {
        const response = await fetch('/api/clientes/reload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            Logger.log(`Cache recarregado: ${data.total} clientes`, 'success');
            if (clientAutocomplete) {
                clientAutocomplete.reloadCache();
            }
            NotificationManager.show(`Cache recarregado: ${data.total} clientes`, 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Logger.handleError('Erro ao recarregar cache', error);
    }
}

async function showClientStats() {
    try {
        const response = await fetch('/api/clientes/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            const message = `Estatísticas dos Clientes:

Total: ${stats.total_clientes}
Com empresa: ${stats.com_empresa}
Com WhatsApp: ${stats.com_whatsapp}
Sem telefone: ${stats.sem_telefone}
Empresas únicas: ${stats.empresas_unicas}

${stats.cache_info}`;
            
            alert(message);
        }
    } catch (error) {
        Logger.handleError('Erro ao obter estatísticas', error);
        alert('Erro ao obter estatísticas');
    }
}

function clearAutocompleteSelection() {
    if (clientAutocomplete) {
        document.getElementById('convidado').value = '';
        clientAutocomplete.clearSelection();
        Logger.log('Seleção limpa', 'info');
    }
}

// ================================================
// FUNÇÕES DE DEBUG APRIMORADAS
// ================================================
// ================================================
// FUNÇÕES DE DEBUG APRIMORADAS
// ================================================
function debugAgenda() {
    if (!agenda) {
        console.log('Agenda não inicializada');
        return;
    }
    console.log('Estado atual da agenda:', agenda.getSystemStatus());
}

function forceReload() {
    if (agenda) {
        agenda.loadMeetings().then(() => {
            agenda.applyFilters();
            Logger.log('Dados recarregados com sucesso', 'success');
        }).catch(error => {
            Logger.handleError('Erro ao recarregar', error);
        });
    }
}

function testAutoSend() {
    if (agenda) {
        return agenda.testAutoSend();
    }
}

function debugMeetingDetails(meetingId) {
    console.log('=== DEBUG: DETALHES DA REUNIÃO ===');
    
    if (!agenda) {
        console.log('❌ Agenda não inicializada');
        return;
    }
    
    if (!meetingId) {
        console.log('❌ ID da reunião não fornecido');
        console.log('💡 Uso: debugMeetingDetails(123)');
        return;
    }
    
    const meeting = agenda.state.meetings.find(m => m.id == meetingId);
    
    if (!meeting) {
        console.log(`❌ Reunião ${meetingId} não encontrada`);
        return;
    }
    
    console.log('📊 Dados da reunião:', meeting);
    console.log('📅 Data/Hora:', Utils.formatDateTime(meeting.datetime));
    console.log('📞 Telefone:', meeting.phone || 'Não informado');
    console.log('✅ Status:', meeting.status_confirmacao || 'pending');
    
    // Tenta buscar respostas
    fetch(`/agenda/responses/${meetingId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.responses) {
                console.log(`📬 Respostas (${data.responses.length}):`, data.responses);
            } else {
                console.log('📭 Nenhuma resposta encontrada');
            }
        })
        .catch(err => console.log('❌ Erro ao buscar respostas:', err.message));
}

// ================================================
// INICIALIZAÇÃO DA APLICAÇÃO
// ================================================
document.addEventListener('DOMContentLoaded', () => {
    try {
        Logger.log('Inicializando Agenda Executiva v4.2...', 'info');
        
        agenda = new AgendaExecutiva();
        
        // Configura ambiente de desenvolvimento
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            window.agenda = agenda;
            window.debugAgenda = debugAgenda;
            window.forceReload = forceReload;
            window.testAutoSend = testAutoSend;
            window.debugMeetingDetails = debugMeetingDetails;
            window.reloadClientCache = reloadClientCache;
            window.showClientStats = showClientStats;
            window.clearAutocompleteSelection = clearAutocompleteSelection;
            
            Logger.log('Agenda Executiva carregada em modo desenvolvimento', 'success');
            Logger.log('Funções disponíveis: debugAgenda(), testAutoSend(), debugMeetingDetails(), reloadClientCache(), showClientStats()', 'info');
        }
        
        Logger.log('Agenda Executiva v4.2 inicializada com sucesso!', 'success');
        
    } catch (error) {
        Logger.handleError('Erro crítico na inicialização', error);
        alert('Erro crítico na inicialização do sistema. Recarregue a página.');
    }
});

// ================================================
// TRATAMENTO DE ERROS GLOBAIS
// ================================================
window.addEventListener('error', (event) => {
    Logger.handleError('Erro JavaScript não tratado', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
});

window.addEventListener('unhandledrejection', (event) => {
    Logger.handleError('Promise rejeitada não tratada', event.reason);
    event.preventDefault();
});

// ================================================
// INTEGRAÇÃO COM MODAL EXISTENTE
// ================================================
const originalOpenModalFunc = window.openModal;
window.openModal = function() {
    if (originalOpenModalFunc) {
        originalOpenModalFunc();
    } else {
        const modal = document.getElementById('modal');
        if (modal) modal.style.display = 'flex';
    }
    
    setTimeout(() => {
        if (agenda && !agenda.clientAutocomplete) {
            agenda.initializeClientAutocomplete();
        }
    }, 100);
};

// ================================================
// EXPORT PARA MÓDULOS
// ================================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        AgendaExecutiva, 
        Utils, 
        Logger, 
        NotificationManager, 
        ApiManager, 
        ModalManager, 
        FormValidator, 
        ClientAutocomplete 
    };
}

/**
 * ================================================
 * RESUMO DAS MELHORIAS v4.2
 * ================================================
 * 
 * ✅ ESTRUTURA ORGANIZADA:
 * - Código dividido em classes modulares e especializadas
 * - Separação clara de responsabilidades
 * - Funções utilitárias centralizadas
 * 
 * ✅ CORREÇÕES IMPLEMENTADAS:
 * - Todos os erros de sintaxe removidos
 * - Função ensureString() corrigida definitivamente
 * - Autocomplete integrado corretamente
 * - Gerenciamento de estado melhorado
 * 
 * ✅ MELHORIAS DE PERFORMANCE:
 * - Cache de elementos DOM otimizado
 * - Debounce implementado corretamente
 * - API calls com retry automático
 * - Auto-refresh inteligente
 * 
 * ✅ FUNCIONALIDADES MANTIDAS:
 * - Todas as funcionalidades originais preservadas
 * - Compatibilidade com backend Python
 * - Interface responsiva
 * - Sistema de notificações
 * 
 * ✅ MELHOR MANUTENIBILIDADE:
 * - Código bem documentado
 * - Logging centralizado
 * - Tratamento de erros robusto
 * - Funções de debug aprimoradas
 * 
 * 🎯 RESULTADO:
 * Código limpo, organizado e livre de erros,
 * mantendo todas as funcionalidades originais
 * com melhor performance e manutenibilidade.
 * ================================================
 */

// ================================================
// CORREÇÃO PRINCIPAL: Sistema de Monitoramento e Status Automático
// ================================================

// Substitua a classe MonitoringManager existente por esta versão corrigida:
// ================================================
// CORREÇÃO PRINCIPAL: Sistema de Monitoramento e Status Automático
// ================================================

// Substitua a classe MonitoringManager existente por esta versão corrigida:
class MonitoringManager {
    constructor(agenda) {
        this.agenda = agenda;
        this.isMonitoring = false;
        this.lastUpdateTime = null;
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = 3;
        this.updateInterval = 5000; 
        this.retryDelay = 5000;
        this.lastStatusCheck = {};
        this.monitoringStartTime = null;
        this.lastResponseCheck = null;
        this.monitoringInterval = null;
        this.healthCheckInterval = null;
        
        this.config = {
            endpoints: {
                status: '/whatsapp/status',
                logs: '/whatsapp/logs',
                meetings: '/agenda/dados',
                responses: '/agenda/check-new-responses'
            },
            timeouts: {
                request: 8000, // Reduzido de 10s para 8s
                retry: 3000,   // Reduzido de 5s para 3s
                health: 300000 // Aumentado para 5 minutos
            }
        };
    }

    async startMonitoring() {
        if (this.isMonitoring) {
            Logger.log('Monitoramento já está ativo', 'warn');
            return;
        }

        Logger.log('Iniciando monitoramento inteligente...', 'info');
        
        this.isMonitoring = true;
        this.monitoringStartTime = new Date();
        this.consecutiveErrors = 0;
        this.lastResponseCheck = new Date();
        
        // Primeira verificação com delay para evitar sobrecarga inicial
        setTimeout(() => {
            this.performMonitoringCycle();
        }, 2000);
        
        // Ciclo principal
        this.monitoringInterval = setInterval(() => {
            this.performMonitoringCycle();
        }, this.updateInterval);
        
        // Health check menos frequente
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, this.config.timeouts.health);
        
        Logger.log('Monitoramento inteligente iniciado', 'success');
    }

    async performMonitoringCycle() {
        // Evita execução simultânea
        if (this.isProcessing) {
            Logger.log('Ciclo anterior ainda em execução, aguardando...', 'debug');
            return;
        }

        this.isProcessing = true;
        const startTime = Date.now();
        
        try {
            Logger.log('Executando ciclo de monitoramento...', 'info');
            
            // 1. Verifica status do WhatsApp primeiro (mais rápido)
            const whatsappStatus = await this.updateWhatsAppStatus();
            
            if (!whatsappStatus.connected) {
                Logger.log('WhatsApp desconectado, pulando verificação de respostas', 'warn');
                this.updateMonitoringUI({
                    isActive: this.isMonitoring,
                    phoneCount: 0,
                    statusMessage: 'WhatsApp desconectado'
                });
                return { success: false, error: 'WhatsApp disconnected' };
            }
            
            // 2. Verifica novas respostas apenas se WhatsApp está conectado
            const newResponses = await this.checkNewResponses();
            
            // 3. Se há novas respostas, recarrega reuniões
            if (newResponses && newResponses.length > 0) {
                Logger.log(`${newResponses.length} nova(s) resposta(s) processada(s)`, 'success');
                await this.reloadMeetingsData();
                this.notifyNewResponses(newResponses);
            }
            
            // 4. Atualiza UI
            this.updateMonitoringUI({
                isActive: this.isMonitoring,
                phoneCount: newResponses ? newResponses.length : 0,
                statusMessage: newResponses && newResponses.length > 0 ? 
                    `${newResponses.length} resposta(s) processada(s)` : 
                    'Monitorando respostas...'
            });
            
            // Reset contador de erros
            this.consecutiveErrors = 0;
            this.lastUpdateTime = new Date();
            
            const duration = Date.now() - startTime;
            Logger.log(`Ciclo completado em ${duration}ms`, 'success');
            
            return {
                success: true,
                duration,
                newResponses: newResponses || [],
                whatsappStatus
            };
            
        } catch (error) {
            this.consecutiveErrors++;
            Logger.handleError(`Erro no ciclo de monitoramento (tentativa ${this.consecutiveErrors})`, error);
            
            if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                Logger.log('Muitos erros consecutivos, pausando monitoramento temporariamente', 'warn');
                this.pauseMonitoring();
            }
            
            return {
                success: false,
                error: error.message,
                consecutiveErrors: this.consecutiveErrors
            };
        } finally {
            this.isProcessing = false;
        }
    }

    async checkNewResponses() {
        try {
            // 1. Busca mudanças dos últimos 5 minutos
            const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
            
            Logger.log(`🔍 Verificando mudanças desde ${fiveMinutesAgo}`, 'info');
            
            const response = await fetch(`/agenda/recent-changes?since=${encodeURIComponent(fiveMinutesAgo)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                Logger.log(`⚠️ Backend retornou erro: ${data.message}`, 'warn');
                return [];
            }
            
            if (!data.changes || data.changes.length === 0) {
                Logger.log('📭 Nenhuma mudança detectada', 'debug');
                return [];
            }
            
            Logger.log(`📬 ${data.changes.length} mudança(s) detectada(s)`, 'success');
            
            // 2. CRÍTICO: Recarrega TODAS as reuniões ANTES de processar
            await this.reloadMeetingsData();
            
            // 3. Processa cada mudança individualmente
            const processedResponses = [];
            
            for (const change of data.changes) {
                try {
                    Logger.log(`📝 Processando reunião ${change.meeting_id}: ${change.status}`, 'info');
                    
                    // Atualiza UI imediatamente
                    await this.updateMeetingInUI(change.meeting_id, change.status);
                    
                    processedResponses.push({
                        meeting_id: change.meeting_id,
                        new_status: change.status,
                        updated_at: change.updated_at
                    });
                    
                } catch (error) {
                    Logger.log(`❌ Erro ao processar reunião ${change.meeting_id}: ${error.message}`, 'error');
                }
            }
            
            // 4. Notifica usuário se houver mudanças
            if (processedResponses.length > 0) {
                this.notifyNewResponses(processedResponses);
            }
            
            return processedResponses;
            
        } catch (error) {
            Logger.log(`💥 Erro ao verificar mudanças: ${error.message}`, 'error');
            return [];
        }
    }

    async checkMeetingResponse(meeting) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout por reunião
            
            const response = await fetch(`/agenda/responses/${meeting.id}`, {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const responsesData = await response.json();
            
            if (responsesData.success && responsesData.responses && responsesData.responses.length > 0) {
                const latestResponse = responsesData.responses[responsesData.responses.length - 1];
                const currentStatus = meeting.status_confirmacao || 'pending';
                
                // Verifica mudança com threshold mais conservador
                if (latestResponse.status && 
                    latestResponse.status !== currentStatus && 
                    latestResponse.confidence >= 0.3) {
                    
                    Logger.log(`Mudança detectada: Reunião ${meeting.id} (${currentStatus} -> ${latestResponse.status})`, 'success');
                    
                    const processResult = await this.processNewResponse({
                        ...latestResponse,
                        meeting_id: meeting.id
                    });
                    
                    if (processResult.success) {
                        return {
                            meeting_id: meeting.id,
                            meeting_title: meeting.title,
                            old_status: currentStatus,
                            new_status: latestResponse.status,
                            confidence: latestResponse.confidence,
                            response_text: latestResponse.response_text
                        };
                    }
                }
            }
            
            return null;
            
        } catch (error) {
            // Não loga erros de timeout/conexão para evitar spam
            if (!error.message.includes('aborted') && !error.message.includes('timeout')) {
                Logger.log(`Erro ao verificar reunião ${meeting.id}: ${error.message}`, 'debug');
            }
            throw error;
        }
    }

    async processNewResponse(responseData) {
        try {
            const meetingId = responseData.meeting_id;
            const newStatus = responseData.status;
            
            if (!meetingId || !newStatus) {
                Logger.log('Dados insuficientes para processar resposta', 'warn');
                return { success: false };
            }
            
            Logger.log(`Processando resposta: Reunião ${meetingId} -> Status: ${newStatus}`, 'info');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout
            
            const response = await fetch(`/agenda/manual-confirmation/${meetingId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    status: newStatus,
                    automated: true,
                    response_id: responseData.id,
                    confidence: responseData.confidence || 0
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const updateResult = await response.json();
            
            if (updateResult.success) {
                Logger.log(`Status da reunião ${meetingId} atualizado automaticamente para: ${newStatus}`, 'success');
                
                // Atualiza UI de forma assíncrona para não bloquear
                setTimeout(() => {
                    this.updateMeetingInUI(meetingId, newStatus);
                }, 100);
                
                return {
                    success: true,
                    meetingId,
                    newStatus,
                    automated: true
                };
            } else {
                throw new Error(updateResult.message || 'Falha ao atualizar status');
            }
            
        } catch (error) {
            Logger.handleError(`Erro ao processar resposta para reunião ${responseData.meeting_id}`, error);
            return {
                success: false,
                error: error.message,
                meetingId: responseData.meeting_id
            };
        }
    }

    notifyNewResponses(responses) {
        try {
            const confirmedCount = responses.filter(r => r.new_status === 'confirmed').length;
            const declinedCount = responses.filter(r => r.new_status === 'declined').length;
            const pendingCount = responses.filter(r => r.new_status === 'pending').length;
            
            let message = 'Novas respostas processadas: ';
            const parts = [];
            
            if (confirmedCount > 0) parts.push(`${confirmedCount} confirmação(ões)`);
            if (declinedCount > 0) parts.push(`${declinedCount} recusa(s)`);
            if (pendingCount > 0) parts.push(`${pendingCount} pendente(s)`);
            
            message += parts.join(', ');
            
            // Notificação mais discreta
            //if (typeof NotificationManager !== 'undefined') {
                //NotificationManager.show(message, 'info', 2000);
            //}
            
            Logger.log(`Resumo das respostas: ${confirmedCount} confirmadas, ${declinedCount} recusadas, ${pendingCount} pendentes`, 'success');
            
        } catch (error) {
            Logger.log(`Erro ao notificar novas respostas: ${error.message}`, 'warn');
        }
    }

    async updateWhatsAppStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeouts.request);
            
            const response = await fetch('/whatsapp/status', {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Atualiza status na agenda de forma segura
            if (this.agenda && typeof this.agenda.updateConnectionStatus === 'function') {
                this.agenda.updateConnectionStatus(data);
            }
            
            return {
                connected: data.connected === true,
                status: data.status_message || 'Desconhecido'
            };
            
        } catch (error) {
            Logger.log(`Erro ao verificar WhatsApp: ${error.message}`, 'warn');
            return {
                connected: false,
                status: 'Erro de conexão'
            };
        }
    }

    async reloadMeetingsData() {
        try {
            Logger.log('Recarregando dados das reuniões...', 'info');
            
            if (this.agenda && typeof this.agenda.loadMeetings === 'function') {
                await this.agenda.loadMeetings();
                
                if (typeof this.agenda.applyFilters === 'function') {
                    this.agenda.applyFilters();
                }
                
                Logger.log('Reuniões recarregadas com sucesso', 'success');
            }
        } catch (error) {
            Logger.handleError('Erro ao recarregar reuniões', error);
        }
    }

    updateMonitoringUI(monitoringStatus) {
        try {
            const elements = {
                indicator: document.getElementById('monitoringIndicator'),
                text: document.getElementById('monitoringText'),
                phones: document.getElementById('monitoredPhones')
            };
            
            if (elements.indicator) {
                elements.indicator.className = monitoringStatus.isActive ? 
                    'monitoring-indicator active' : 
                    'monitoring-indicator inactive';
            }
            
            if (elements.text) {
                elements.text.textContent = monitoringStatus.statusMessage;
            }
            
            if (elements.phones) {
                const phoneText = monitoringStatus.phoneCount > 0 ? 
                    `${monitoringStatus.phoneCount} atividade(s)` : 
                    'Monitorando...';
                elements.phones.textContent = phoneText;
            }
            
            // Atualiza estado na agenda de forma segura
            if (this.agenda && typeof this.agenda.setState === 'function') {
                this.agenda.setState({ 
                    monitoringActive: monitoringStatus.isActive,
                    monitoredPhones: monitoringStatus.phoneCount
                });
            }
            
        } catch (error) {
            Logger.log(`Erro ao atualizar UI: ${error.message}`, 'debug');
        }
    }

    async performHealthCheck() {
        try {
            const uptime = Date.now() - this.monitoringStartTime;
            const uptimeMinutes = Math.floor(uptime / (1000 * 60));
            
            Logger.log(`Health check - Monitoramento ativo por ${uptimeMinutes} minutos`, 'info');
            
            // Health check mais simples
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            try {
                const response = await fetch('/whatsapp/status', {
                    method: 'GET',
                    signal: controller.signal,
                    headers: { 'Content-Type': 'application/json' }
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    Logger.log('Conectividade OK', 'success');
                    
                    // Normaliza intervalo se estava aumentado por erros
                    if (this.updateInterval > 30000) {
                        this.updateInterval = 30000;
                        Logger.log('Frequência de monitoramento normalizada', 'info');
                        this.restartMonitoring();
                    }
                } else {
                    Logger.log(`Status de conectividade: ${response.status}`, 'warn');
                }
            } catch (healthError) {
                Logger.log(`Problemas de conectividade: ${healthError.message}`, 'error');
            }
            
        } catch (error) {
            Logger.log(`Erro no health check: ${error.message}`, 'error');
        }
    }

   async updateMeetingInUI(meetingId, newStatus) {
    try {
        Logger.log(`🔄 Atualizando UI: Reunião ${meetingId} -> ${newStatus}`, 'info');

        // ============================================
        // ETAPA 1: BUSCA DADOS FRESCOS DO SERVIDOR
        // ============================================
        const meetingResponse = await fetch(`/agenda/meeting/${meetingId}`);

        if (!meetingResponse.ok) {
            throw new Error(`HTTP ${meetingResponse.status}: ${meetingResponse.statusText}`);
        }

        const meetingData = await meetingResponse.json();

        if (!meetingData || !meetingData.success) {
            throw new Error(meetingData?.message || 'Erro ao buscar dados da reunião');
        }

        const updatedMeeting = meetingData.meeting;
        Logger.log(`✅ Dados frescos: ID=${updatedMeeting.id}, Status=${updatedMeeting.status_confirmacao}`, 'success');

        // ============================================
        // ETAPA 2: ATUALIZA ESTADO LOCAL
        // ============================================
        if (this.agenda?.state?.meetings) {
            const meetingIndex = this.agenda.state.meetings.findIndex(m =>
                String(m.id) === String(meetingId)
            );

            if (meetingIndex !== -1) {
                this.agenda.state.meetings[meetingIndex] = updatedMeeting;
                Logger.log(`📝 Estado local atualizado (índice ${meetingIndex})`, 'success');
            } else {
                Logger.log(`⚠️ Reunião ${meetingId} não encontrada no array local`, 'warn');
            }
        }

        // ============================================
        // ETAPA 3: ATUALIZA MODAL SE ABERTO
        // ============================================
        const modal = document.getElementById('meetingDetailsModal');
        const modalAberto = modal && (modal.style.display === 'block' || modal.style.display === 'flex');
        const mesmaReuniao = this.agenda?.activeModalMeetingId === meetingId;

        if (modalAberto && mesmaReuniao) {
            Logger.log(`🎯 Modal aberto — atualizando conteúdo...`, 'info');

            try {
                const responsesResponse = await fetch(`/agenda/responses/${meetingId}`);
                if (!responsesResponse.ok) throw new Error(`HTTP ${responsesResponse.status}`);

                const responsesData = await responsesResponse.json();
                const responses = responsesData.success ? (responsesData.responses || []) : [];

                this.agenda.renderMeetingDetails(updatedMeeting, responses);
                Logger.log(`✨ Modal re-renderizado com ${responses.length} resposta(s)`, 'success');

                // Feedback visual suave
                setTimeout(() => {
                    const statusElements = document.querySelectorAll('.confirmation-status');
                    statusElements.forEach(el => {
                        el.style.transition = 'all 0.5s ease';
                        el.style.transform = 'scale(1.08)';
                        el.style.background = '#dcfce7';
                        el.style.boxShadow = '0 0 12px rgba(16, 185, 129, 0.4)';
                        setTimeout(() => {
                            el.style.transform = '';
                            el.style.background = '';
                            el.style.boxShadow = '';
                        }, 1200);
                    });
                }, 150);
            } catch (modalError) {
                Logger.log(`⚠️ Erro ao atualizar modal: ${modalError.message}`, 'warn');
            }
        }

        // ============================================
        // ETAPA 4: ATUALIZA LISTA PRINCIPAL
        // ============================================
        if (this.agenda && typeof this.agenda.applyFilters === 'function') {
            this.agenda.applyFilters();
            Logger.log(`🔄 Lista principal atualizada`, 'success');

            // Atualiza visualmente o badge de status no card
            const statusEls = document.querySelectorAll('.meeting-card .confirmation-status');
            statusEls.forEach(el => {
                el.className = `confirmation-status status-${newStatus}`;
                el.textContent = this.agenda.getConfirmationStatusText(newStatus);
            });
        }

        // ============================================
        // ETAPA 5: DESTAQUE VISUAL NO CARD
        // ============================================
        setTimeout(() => {
            try {
                let card = null;
                const allButtons = document.querySelectorAll('button[onclick]');
                for (const button of allButtons) {
                    const onclick = button.getAttribute('onclick');
                    if (onclick && onclick.includes(`openMeetingDetailsModal(${meetingId})`)) {
                        card = button.closest('.meeting-card');
                        break;
                    }
                }

                if (!card) {
                    card = document.querySelector(`.meeting-card[data-meeting-id="${meetingId}"]`);
                }

                if (card) {
                    card.style.transition = 'all 0.5s ease';
                    card.style.transform = 'scale(1.02)';
                    card.style.boxShadow = '0 8px 24px rgba(16, 185, 129, 0.4)';
                    card.style.borderColor = '#10b981';

                    setTimeout(() => {
                        card.style.transform = '';
                        card.style.boxShadow = '';
                        card.style.borderColor = '';
                    }, 1500);
                } else {
                    Logger.log(`ℹ️ Card da reunião ${meetingId} não encontrado (pode estar filtrado)`, 'debug');
                }
            } catch (cardError) {
                Logger.log(`⚠️ Erro ao destacar card: ${cardError.message}`, 'debug');
            }
        }, 200);

        Logger.log(`✅ UI sincronizada com sucesso para reunião ${meetingId}`, 'success');
        return true;

    } catch (error) {
        Logger.log(`❌ Erro ao atualizar UI da reunião ${meetingId}: ${error.message}`, 'error');

        try {
            if (this.agenda && typeof this.agenda.applyFilters === 'function') {
                Logger.log(`🔄 Recuperação: atualizando lista...`, 'info');
                await this.agenda.applyFilters();
            }
        } catch (recoveryError) {
            Logger.log(`❌ Recuperação falhou: ${recoveryError.message}`, 'error');
        }

        return false;
    }
}


// Pausa temporária do monitoramento
pauseMonitoring() {
    Logger.log('Pausando monitoramento temporariamente...', 'warn');
    
    if (this.monitoringInterval) {
        clearInterval(this.monitoringInterval);
        this.monitoringInterval = null;
    }
    
    setTimeout(() => {
        if (this.isMonitoring) {
            Logger.log('Reiniciando monitoramento...', 'info');
            this.updateInterval = Math.min(this.updateInterval * 1.5, 120000);
            this.consecutiveErrors = 0;
            
            this.monitoringInterval = setInterval(() => {
                this.performMonitoringCycle();
            }, this.updateInterval);
        }
    }, 30000);
}

// Reinicia monitoramento
restartMonitoring() {
    if (this.monitoringInterval) {
        clearInterval(this.monitoringInterval);
        this.monitoringInterval = setInterval(() => {
            this.performMonitoringCycle();
        }, this.updateInterval);
    }
}

// Status do monitoramento
getStatus() {
    return {
        isMonitoring: this.isMonitoring,
        uptime: this.monitoringStartTime ? Date.now() - this.monitoringStartTime : 0,
        lastUpdate: this.lastUpdateTime,
        lastResponseCheck: this.lastResponseCheck,
        consecutiveErrors: this.consecutiveErrors,
        updateInterval: this.updateInterval,
        config: this.config,
        isProcessing: this.isProcessing || false
    };
}

// Força atualização
async forceUpdate() {
    Logger.log('Forçando verificação de respostas...', 'info');
    this.lastResponseCheck = new Date(Date.now() - 300000);
    this.consecutiveErrors = 0;
    return await this.performMonitoringCycle();
}

// Para monitoramento
stopMonitoring() {
    if (!this.isMonitoring) return;

    Logger.log('Parando monitoramento...', 'info');
    
    this.isMonitoring = false;
    this.isProcessing = false;
    
    if (this.monitoringInterval) {
        clearInterval(this.monitoringInterval);
        this.monitoringInterval = null;
    }
    
    if (this.healthCheckInterval) {
        clearInterval(this.healthCheckInterval);
        this.healthCheckInterval = null;
    }
    
    Logger.log('Monitoramento parado', 'success');
}
} // FIM DA CLASSE MonitoringManager

// ============================================
// INTEGRAÇÃO COM AgendaExecutiva
// ============================================
if (typeof AgendaExecutiva !== 'undefined') {
    // Inicializa monitoramento
    AgendaExecutiva.prototype.initializeMonitoring = function() {
        try {
            if (!this.monitoringManager) {
                this.monitoringManager = new MonitoringManager(this);
                Logger.log('Gerenciador de monitoramento inicializado', 'success');
            }
            return this.monitoringManager;
        } catch (error) {
            Logger.handleError('Erro ao inicializar monitoramento', error);
            return null;
        }
    };

    // Atualiza status do monitoramento
    AgendaExecutiva.prototype.updateMonitoringStatus = async function() {
        try {
            if (!this.monitoringManager) {
                this.initializeMonitoring();
            }
            
            if (this.monitoringManager && !this.monitoringManager.isMonitoring) {
                await this.monitoringManager.startMonitoring();
            }
            
            return this.monitoringManager ? this.monitoringManager.getStatus() : null;
        } catch (error) {
            Logger.handleError('Erro ao atualizar status do monitoramento', error);
            return null;
        }
    };

    // Para monitoramento
    AgendaExecutiva.prototype.stopMonitoring = function() {
        try {
            if (this.monitoringManager) {
                this.monitoringManager.stopMonitoring();
            }
        } catch (error) {
            Logger.handleError('Erro ao parar monitoramento', error);
        }
    };

    // Auto-refresh melhorado
    AgendaExecutiva.prototype.startAutoRefresh = function() {
        try {
            this.stopAutoRefresh();
            
            Logger.log('Iniciando auto-refresh...', 'info');
            
            this.intervals = this.intervals || {};
            
            // Auto-refresh de reuniões (menos frequente)
            this.intervals.autoRefresh = setInterval(async () => {
                try {
                    if (this.hasWeekChanged && this.hasWeekChanged()) {
                        Logger.log('Nova semana detectada, recarregando...', 'info');
                        await this.loadMeetings();
                        if (this.applyFilters) this.applyFilters();
                        if (this.updateWeekInfo) this.updateWeekInfo();
                    }
                } catch (error) {
                    Logger.handleError('Erro no auto-refresh', error);
                }
            }, this.config?.autoRefreshInterval || 300000);

            // Inicializa monitoramento após delay
            setTimeout(() => {
                try {
                    this.initializeMonitoring();
                    if (this.monitoringManager) {
                        this.monitoringManager.startMonitoring();
                    }
                } catch (error) {
                    Logger.handleError('Erro ao iniciar monitoramento', error);
                }
            }, 3000);

            // Status WhatsApp (menos frequente)
            this.intervals.statusUpdate = setInterval(async () => {
                try {
                    if (this.state?.whatsappConnected && this.updateWhatsAppStatusIndicator) {
                        await this.updateWhatsAppStatusIndicator();
                    }
                } catch (error) {
                    // Silencia erros
                }
            }, 60000);

            Logger.log('Auto-refresh iniciado', 'success');
        } catch (error) {
            Logger.handleError('Erro ao iniciar auto-refresh', error);
        }
    };
}

// ============================================
// FUNÇÕES GLOBAIS DE CONTROLE
// ============================================
function startMonitoring() {
    try {
        if (typeof agenda !== 'undefined' && agenda) {
            if (agenda.monitoringManager) {
                agenda.monitoringManager.startMonitoring();
            } else {
                agenda.initializeMonitoring();
                if (agenda.monitoringManager) {
                    agenda.monitoringManager.startMonitoring();
                }
            }
            Logger.log('✅ Monitoramento iniciado manualmente', 'success');
        } else {
            console.warn('⚠️ Agenda não disponível');
        }
    } catch (error) {
        console.error('❌ Erro ao iniciar monitoramento:', error);
    }
}

function stopMonitoring() {
    try {
        if (typeof agenda !== 'undefined' && agenda && agenda.monitoringManager) {
            agenda.monitoringManager.stopMonitoring();
            Logger.log('✅ Monitoramento parado manualmente', 'success');
        }
    } catch (error) {
        console.error('❌ Erro ao parar monitoramento:', error);
    }
}

function getMonitoringStatus() {
    try {
        if (typeof agenda !== 'undefined' && agenda && agenda.monitoringManager) {
            const status = agenda.monitoringManager.getStatus();
            console.log('📊 STATUS DO MONITORAMENTO:', status);
            return status;
        }
        console.warn('⚠️ Monitoramento não inicializado');
        return { isMonitoring: false, error: 'Não inicializado' };
    } catch (error) {
        console.error('❌ Erro:', error);
        return { isMonitoring: false, error: error.message };
    }
}

function forceMonitoringUpdate() {
    try {
        if (typeof agenda !== 'undefined' && agenda && agenda.monitoringManager) {
            Logger.log('🔄 Forçando verificação manual...', 'info');
            return agenda.monitoringManager.forceUpdate();
        }
        console.warn('⚠️ Monitoramento não disponível');
        return Promise.resolve({ success: false, error: 'Não disponível' });
    } catch (error) {
        console.error('❌ Erro:', error);
        return Promise.resolve({ success: false, error: error.message });
    }
}

// ============================================
// FUNÇÕES DE DEBUG
// ============================================
function debugMonitoringStatus() {
    console.log('=== DEBUG: STATUS DO MONITORAMENTO ===');
    
    if (typeof agenda === 'undefined' || !agenda) {
        console.log('❌ Agenda não inicializada');
        return;
    }
    
    if (!agenda.monitoringManager) {
        console.log('❌ MonitoringManager não existe');
        return;
    }
    
    const status = agenda.monitoringManager.getStatus();
    console.log('📊 Status:', status);
    console.log('🔄 Monitorando:', status.isMonitoring ? 'SIM ✅' : 'NÃO ❌');
    console.log('⏱️ Uptime:', Math.floor(status.uptime / 1000), 'segundos');
    console.log('🔁 Intervalo:', status.updateInterval / 1000, 'segundos');
    console.log('❌ Erros consecutivos:', status.consecutiveErrors);
    console.log('📅 Última verificação:', status.lastResponseCheck);
    
    console.log('\n🔄 Forçando verificação...');
    agenda.monitoringManager.forceUpdate().then(result => {
        console.log('✅ Resultado:', result);
    });
}

function testMonitoringCycle() {
    console.log('=== TESTE: CICLO DE MONITORAMENTO ===');
    
    if (typeof agenda === 'undefined' || !agenda || !agenda.monitoringManager) {
        console.log('❌ Monitoramento não disponível');
        return;
    }
    
    console.log('🚀 Iniciando ciclo de teste...');
    agenda.monitoringManager.performMonitoringCycle().then(result => {
        console.log('📊 Resultado do ciclo:', result);
        console.log('✅ Sucesso:', result.success ? 'SIM' : 'NÃO');
        console.log('⏱️ Duração:', result.duration, 'ms');
        console.log('📬 Novas respostas:', result.newResponses?.length || 0);
    });
}

function checkMeetingsWithPhone() {
    console.log('=== REUNIÕES COM TELEFONE ===');
    
    if (typeof agenda === 'undefined' || !agenda) {
        console.log('❌ Agenda não inicializada');
        return;
    }
    
    const withPhone = agenda.state?.meetings?.filter(m => m.phone) || [];
    console.log(`📊 Total: ${withPhone.length} reuniões com telefone`);
    console.log('');
    
    if (withPhone.length === 0) {
        console.log('ℹ️ Nenhuma reunião com telefone cadastrado');
        return;
    }
    
    withPhone.forEach((meeting, index) => {
        console.log(`${index + 1}. ID: ${meeting.id}`);
        console.log(`   📝 Título: ${meeting.title}`);
        console.log(`   📞 Telefone: ${meeting.phone}`);
        console.log(`   ✅ Status: ${meeting.status_confirmacao || 'pending'}`);
        console.log('');
    });
}

// ============================================
// ESTILOS CSS PARA MONITORAMENTO
// ============================================
const monitoringStyles = `
.monitoring-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    transition: all 0.3s ease;
}

.monitoring-indicator.active {
    background-color: #10b981;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
    animation: pulse 2s infinite;
}

.monitoring-indicator.inactive {
    background-color: #ef4444;
    box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3);
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.monitoring-status {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 14px;
    color: #475569;
}
`;

// Adiciona estilos
try {
    if (typeof document !== 'undefined' && document.head) {
        const existingStyles = document.querySelector('style[data-monitoring]');
        if (existingStyles) {
            existingStyles.remove();
        }
        
        const styleElement = document.createElement('style');
        styleElement.setAttribute('data-monitoring', 'true');
        styleElement.innerHTML = monitoringStyles;
        document.head.appendChild(styleElement);
    }
} catch (error) {
    console.debug('Erro ao adicionar estilos:', error);
}

// Expõe funções globalmente
if (typeof window !== 'undefined') {
    window.debugMonitoringStatus = debugMonitoringStatus;
    window.testMonitoringCycle = testMonitoringCycle;
    window.checkMeetingsWithPhone = checkMeetingsWithPhone;
    window.startMonitoring = startMonitoring;
    window.stopMonitoring = stopMonitoring;
    window.getMonitoringStatus = getMonitoringStatus;
    window.forceMonitoringUpdate = forceMonitoringUpdate;
}

// Log de inicialização
if (typeof Logger !== 'undefined') {
    Logger.log('✅ Sistema de monitoramento carregado e pronto', 'success');
} else {
    console.log('✅ Sistema de monitoramento carregado');
}

// Ajuda no console
console.log('%c🎯 FUNÇÕES DE MONITORAMENTO DISPONÍVEIS:', 'color: #10b981; font-weight: bold; font-size: 14px;');
console.log('%c  • debugMonitoringStatus()', 'color: #3b82f6;', '- Status completo');
console.log('%c  • testMonitoringCycle()', 'color: #3b82f6;', '- Testa um ciclo');
console.log('%c  • checkMeetingsWithPhone()', 'color: #3b82f6;', '- Lista reuniões');
console.log('%c  • startMonitoring()', 'color: #10b981;', '- Inicia monitoramento');
console.log('%c  • stopMonitoring()', 'color: #ef4444;', '- Para monitoramento');
console.log('%c  • getMonitoringStatus()', 'color: #f59e0b;', '- Status atual');
console.log('%c  • forceMonitoringUpdate()', 'color: #8b5cf6;', '- Força verificação');