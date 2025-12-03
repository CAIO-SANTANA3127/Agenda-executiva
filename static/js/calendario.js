let currentDate = new Date();
let allMeetings = [];
let allBirthdays = [];
let allHolidays = [];

// ========== FERIADOS BRASILEIROS FIXOS COM DESCRIÇÕES ==========
const FIXED_HOLIDAYS = [
  { 
    month: 0, day: 1, name: 'Ano Novo', icon: '🎉',
    description: 'Celebração do primeiro dia do ano no calendário gregoriano. Marca o início de um novo ciclo anual e é comemorado em todo o mundo como símbolo de renovação e esperança.'
  },
  { 
    month: 3, day: 21, name: 'Tiradentes', icon: '🇧🇷',
    description: 'Homenagem a Joaquim José da Silva Xavier (Tiradentes), líder da Inconfidência Mineira em 1789. Celebra a luta pela liberdade e independência do Brasil contra o domínio português.'
  },
  { 
    month: 3, day: 5, name: 'Aniversário de Duque de Caxias', icon: '🎂🏰',
    description: 'Comemoração da fundação da cidade de Duque de Caxias em 5 de abril de 1943. A cidade é um importante município da Baixada Fluminense, no Rio de Janeiro.'
  },
  { 
    month: 4, day: 1, name: 'Dia do Trabalho', icon: '👷',
    description: 'Celebração internacional dos direitos trabalhistas e homenagem aos trabalhadores. Marca a luta histórica pela jornada de 8 horas e melhores condições de trabalho.'
  },
  { 
    month: 5, day: 13, name: 'Dia de Santo Antônio', icon: '⛪',
    description: 'Celebração de Santo Antônio, padroeiro de Duque de Caxias. Data importante para a cidade que venera o santo como protetor. Festas e procissões marcam esta data especial no município.'
  },
  { 
    month: 8, day: 7, name: 'Independência do Brasil', icon: '🇧🇷',
    description: 'Comemoração da independência do Brasil em relação a Portugal, proclamada em 7 de setembro de 1822 pelo Príncipe Pedro. Marca o surgimento do Brasil como nação independente.'
  },
  { 
    month: 9, day: 12, name: 'Nossa Senhora Aparecida', icon: '🙏',
    description: 'Festa da padroeira do Brasil, Nossa Senhora Aparecida. Celebra a fé cristã católica e a devoção mariana que é parte importante da cultura brasileira.'
  },
  { 
    month: 10, day: 2, name: 'Finados', icon: '🕯️',
    description: 'Dia de veneração aos fiéis defuntos na tradição cristã católica. Comemorado com visitas aos cemitérios e homenagens aos falecidos e seus legados.'
  },
  { 
    month: 10, day: 15, name: 'Proclamação da República', icon: '🇧🇷',
    description: 'Comemoração da proclamação da República Brasileira em 15 de novembro de 1889. Marca o fim da monarquia e o estabelecimento do regime republicano no Brasil.'
  },
  { 
    month: 10, day: 20, name: 'Consciência Negra', icon: '✊',
    description: 'Homenagem à luta contra a escravidão e celebração da cultura afro-brasileira. Comemora Zumbi dos Palmares, símbolo de resistência, e valoriza as contribuições da população negra.'
  },
  { 
    month: 9, day: 30, name: 'Dia do Comércio', icon: '🏪',
    description: 'Celebração da classe comerciária brasileira. Reconhece a importância do comércio para a economia nacional e homenageia os comerciantes por suas contribuições econômicas.'
  },
  { 
    month: 11, day: 25, name: 'Natal', icon: '🎄',
    description: 'Celebração do nascimento de Jesus Cristo. É uma das principais festas cristãs e foi incorporada à cultura brasileira como período de confraternização familiar e solidariedade.'
  }
];

// ========== CÁLCULO DE FERIADOS MÓVEIS ==========

// Algoritmo de Computus para calcular Páscoa
function calculateEaster(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}

// Gerar feriados móveis do ano
function getMovableHolidays(year) {
  const easter = calculateEaster(year);
  const holidays = [];
  
  // ========== PERÍODO DO CARNAVAL (5 DIAS) ==========
  // Carnaval Sábado (50 dias antes de Páscoa)
  const carnivalSaturday = new Date(easter);
  carnivalSaturday.setDate(carnivalSaturday.getDate() - 50);
  holidays.push({
    month: carnivalSaturday.getMonth(),
    day: carnivalSaturday.getDate(),
    name: 'Carnaval - Sábado',
    icon: '🎭',
    isCarnavalStart: true,
    description: 'Início oficial do período de Carnaval. Primeira noite da maior festa popular brasileira, marcada por desfiles, fantasias, música e alegria nas ruas.'
  });

  // Carnaval Domingo (49 dias antes de Páscoa)
  const carnivalSunday = new Date(easter);
  carnivalSunday.setDate(carnivalSunday.getDate() - 49);
  holidays.push({
    month: carnivalSunday.getMonth(),
    day: carnivalSunday.getDate(),
    name: 'Carnaval - Domingo',
    icon: '🎭',
    isCarnavalPart: true,
    description: 'Auge da celebração do Carnaval. Noite de apogeu das festas de rua, desfiles de escolas de samba e apresentações culturais em todo o Brasil.'
  });

  // Carnaval Segunda-feira (48 dias antes de Páscoa)
  const carnivalMonday = new Date(easter);
  carnivalMonday.setDate(carnivalMonday.getDate() - 48);
  holidays.push({
    month: carnivalMonday.getMonth(),
    day: carnivalMonday.getDate(),
    name: 'Carnaval - Segunda-feira',
    icon: '🎭',
    isCarnavalPart: true,
    description: 'Continuação da festa de Carnaval. Dia de encerramento da programação principal com apresentações de blocos, desfiles e celebrações nas ruas.'
  });

  // Carnaval Terça-feira (47 dias antes de Páscoa)
  const carnivalTuesday = new Date(easter);
  carnivalTuesday.setDate(carnivalTuesday.getDate() - 47);
  holidays.push({
    month: carnivalTuesday.getMonth(),
    day: carnivalTuesday.getDate(),
    name: 'Carnaval - Terça-feira',
    icon: '🎭',
    isCarnavalEnd: true,
    description: 'Terça-feira de Carnaval - Última noite antes da Quarta-feira de Cinzas. Encerramento das festas carnavalescas com apresentações finais e celebrações.'
  });

  // Carnaval Quarta-feira (46 dias antes de Páscoa)
  const carnivalWednesday = new Date(easter);
  carnivalWednesday.setDate(carnivalWednesday.getDate() - 46);
  holidays.push({
    month: carnivalWednesday.getMonth(),
    day: carnivalWednesday.getDate(),
    name: 'Carnaval - Quarta-feira de Cinzas',
    icon: '🎭',
    isCarnavalEnd: true,
    description: 'Quarta-feira de Cinzas - Encerramento oficial do Carnaval. Marca o início do período quaresmal na tradição cristã e o fim das celebrações carnavalescas.'
  });
  
  // Sexta-feira Santa (2 dias antes de Páscoa)
  const goodFriday = new Date(easter);
  goodFriday.setDate(goodFriday.getDate() - 2);
  holidays.push({
    month: goodFriday.getMonth(),
    day: goodFriday.getDate(),
    name: 'Sexta-feira Santa',
    icon: '✝️',
    description: 'Comemoração da Paixão e morte de Jesus Cristo. Dia de reflexão espiritual e repouso observado pelos cristãos, marcado por procissões e cerimônias religiosas.'
  });
  
  // Corpus Christi (39 dias após Páscoa)
  const corpusChristi = new Date(easter);
  corpusChristi.setDate(corpusChristi.getDate() + 39);
  holidays.push({
    month: corpusChristi.getMonth(),
    day: corpusChristi.getDate(),
    name: 'Corpus Christi',
    icon: '⛪',
    description: 'Celebração eucarística da Igreja Católica que homenageia o Corpo de Cristo. Comemorada com procissões, tapetes de flores e tradições religiosas nas ruas.'
  });
  
  return holidays;
}

// Renderizar calendário imediatamente ao carregar
function initCalendar() {
  // Carrega feriados primeiro
  loadHolidays();
  // Renderiza o calendário vazio primeiro (rápido)
  renderCalendar();
  // Depois carrega as reuniões e aniversários em background
  loadMeetings();
  loadBirthdays();
}

// Carregar feriados do ano
function loadHolidays() {
  const year = currentDate.getFullYear();
  
  // Limpa feriados anteriores
  allHolidays = [];
  
  // Adiciona feriados fixos
  allHolidays.push(...FIXED_HOLIDAYS);
  
  // Adiciona feriados móveis
  allHolidays.push(...getMovableHolidays(year));
  
  console.log(`🎉 ${allHolidays.length} feriados carregados para ${year}`);
}

// ==================== 🔧 CORREÇÃO PRINCIPAL - CARREGAR REUNIÕES ====================
async function loadMeetings() {
  try {
    const response = await fetch('/api/reunioes');
    const data = await response.json();
    
    // 🆕 CORREÇÃO: A API retorna um objeto, não um array
    console.log('📊 Dados recebidos da API:', data);
    
    // Extrai reuniões e eventos do objeto retornado
    const reunioes = Array.isArray(data.reunioes) ? data.reunioes : [];
    const eventos = Array.isArray(data.eventos) ? data.eventos : [];
    
    // Combina tudo em um único array
    allMeetings = [...reunioes, ...eventos];
    
    console.log(`✅ ${reunioes.length} reuniões carregadas`);
    console.log(`✅ ${eventos.length} eventos carregados`);
    console.log(`✅ Total: ${allMeetings.length} itens no calendário`);
    
    // Re-renderiza com as reuniões carregadas
    renderCalendar();
    
  } catch (error) {
    console.error('❌ Erro ao carregar reuniões:', error);
    // Mantém o calendário visível mesmo com erro
    allMeetings = [];
    renderCalendar();
  }
}

// ==================== 🔧 CORREÇÃO - CARREGAR ANIVERSÁRIOS ====================
async function loadBirthdays() {
  try {
    const response = await fetch('/api/aniversarios');
    const data = await response.json();
    
    // 🆕 CORREÇÃO: Verifica se é array ou objeto
    if (Array.isArray(data)) {
      allBirthdays = data;
    } else {
      // Se vier como objeto, tenta extrair array
      allBirthdays = data.aniversarios || data.birthdays || [];
    }
    
    console.log(`🎂 ${allBirthdays.length} aniversários carregados`);
    
    // Re-renderiza com os aniversários carregados
    renderCalendar();
    
  } catch (error) {
    console.error('❌ Erro ao carregar aniversários:', error);
    // Mantém o calendário visível mesmo com erro
    allBirthdays = [];
    renderCalendar();
  }
}

function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];
  
  // Verificação de segurança - só atualiza se o elemento existir
  const monthElement = document.getElementById('currentMonth');
  if (monthElement) {
    monthElement.textContent = `${monthNames[month]} ${year}`;
  }
  
  const calendarGrid = document.getElementById('calendarGrid');
  if (!calendarGrid) {
    console.error('Elemento calendarGrid não encontrado');
    return;
  }
  
  calendarGrid.innerHTML = '';
  
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const prevLastDay = new Date(year, month, 0);
  
  const firstDayOfWeek = firstDay.getDay();
  const lastDateOfMonth = lastDay.getDate();
  const prevLastDate = prevLastDay.getDate();
  
  // Dias do mês anterior
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const day = prevLastDate - i;
    const dayElement = createDayElement(day, year, month - 1, true);
    calendarGrid.appendChild(dayElement);
  }
  
  // Dias do mês atual
  const today = new Date();
  for (let day = 1; day <= lastDateOfMonth; day++) {
    const isToday = day === today.getDate() && 
                    month === today.getMonth() && 
                    year === today.getFullYear();
    const dayElement = createDayElement(day, year, month, false, isToday);
    calendarGrid.appendChild(dayElement);
  }
  
  // Dias do próximo mês
  const remainingDays = 42 - (firstDayOfWeek + lastDateOfMonth);
  for (let day = 1; day <= remainingDays; day++) {
    const dayElement = createDayElement(day, year, month + 1, true);
    calendarGrid.appendChild(dayElement);
  }
}

// ========== BUSCAR FERIADOS POR DATA ==========
function getHolidaysForDate(month, day) {
  return allHolidays.filter(holiday => {
    return holiday.month === month && holiday.day === day;
  });
}

function createDayElement(day, year, month, otherMonth = false, isToday = false) {
  const dayElement = document.createElement('div');
  dayElement.className = 'calendar-day';
  
  if (otherMonth) dayElement.classList.add('other-month');
  if (isToday) dayElement.classList.add('today');
  
  const dayNumber = document.createElement('div');
  dayNumber.className = 'calendar-day-number';
  dayNumber.textContent = day;
  dayElement.appendChild(dayNumber);
  
  const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const dayMeetings = getMeetingsForDate(dateStr);
  const dayBirthdays = getBirthdaysForDate(month + 1, day);
  const dayHolidays = getHolidaysForDate(month, day);
  
  const hasContent = dayMeetings.length > 0 || dayBirthdays.length > 0 || dayHolidays.length > 0;
  
  // Se tem feriado, marca o dia com classe especial
  if (dayHolidays.length > 0) {
    dayElement.classList.add('holiday');
    const isCarnaval = dayHolidays[0].isCarnavalStart || dayHolidays[0].isCarnavalPart || dayHolidays[0].isCarnavalEnd;
    if (isCarnaval) {
      dayElement.classList.add('carnival');
      dayElement.setAttribute('data-holiday', 'Período de Carnaval');
    } else {
      dayElement.setAttribute('data-holiday', dayHolidays[0].name);
    }
  }
  
  if (hasContent) {
    dayElement.classList.add('has-meetings');
    
    const meetingsContainer = document.createElement('div');
    meetingsContainer.className = 'calendar-meetings';
    
    // ========== MOSTRAR FERIADOS PRIMEIRO ==========
    dayHolidays.forEach(holiday => {
      const holidayItem = document.createElement('div');
      holidayItem.className = 'calendar-meeting-item holiday-item';
      
      // Marca como Carnaval se for parte do período
      if (holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd) {
        holidayItem.classList.add('carnival-item');
      }
      
      holidayItem.innerHTML = `
        <span class="calendar-holiday-icon">${holiday.icon}</span>
        <span class="calendar-meeting-title" title="${holiday.name}">${holiday.name}</span>
      `;
      
      holidayItem.onclick = (e) => {
        e.stopPropagation();
        showHolidayDetails(holiday);
      };
      
      meetingsContainer.appendChild(holidayItem);
    });
    
    // Mostrar aniversários (até 2)
    const displayBirthdays = dayBirthdays.slice(0, 2);
    displayBirthdays.forEach(birthday => {
      const birthdayItem = document.createElement('div');
      birthdayItem.className = 'calendar-meeting-item birthday';
      
      birthdayItem.innerHTML = `
        <span class="calendar-birthday-icon">🎂</span>
        <span class="calendar-meeting-title" title="Aniversário de ${birthday.nome}">${birthday.nome}</span>
      `;
      
      birthdayItem.onclick = (e) => {
        e.stopPropagation();
        showBirthdayDetails(birthday);
      };
      
      meetingsContainer.appendChild(birthdayItem);
    });
    
    // Mostrar reuniões (ajustado para contar feriados e aniversários)
    const itemsBeforeMeetings = dayHolidays.length + displayBirthdays.length;
    const maxMeetings = Math.max(2, 6 - itemsBeforeMeetings);
    const displayMeetings = dayMeetings.slice(0, maxMeetings);
    
    displayMeetings.forEach(meeting => {
      const meetingItem = document.createElement('div');
      meetingItem.className = 'calendar-meeting-item';
      
      // ==================== 🔧 CORREÇÃO: DETECTAR EVENTO vs REUNIÃO ====================
      // Adicionar classes de status (só para reuniões)
      if (meeting.tipo_item !== 'evento') {
        if (meeting.confirmation_status === 'confirmed') {
          meetingItem.classList.add('confirmed');
        } else if (meeting.confirmation_status === 'declined') {
          meetingItem.classList.add('declined');
        } else if (meeting.confirmation_status === 'pending') {
          meetingItem.classList.add('pending');
        }
        
        const statusBadge = document.createElement('div');
        statusBadge.className = `meeting-status-badge ${meeting.confirmation_status || 'pending'}`;
        meetingItem.appendChild(statusBadge);
      } else {
        // Para eventos: adiciona classe especial
        meetingItem.classList.add('evento-item');
      }
      
      // ==================== 🔧 CORREÇÃO: HORÁRIO vs ÍCONE ====================
      let time = '';
      
      if (meeting.tipo_item === 'evento') {
        // Para eventos: mostra ícone de evento
        const eventoIcons = {
          'viagem': '✈️',
          'feira': '🏢',
          'conferencia': '🎤',
          'treinamento': '📚',
          'evento_interno': '🎉',
          'outro': '📅'
        };
        time = eventoIcons[meeting.tipo] || '📅';
      } else {
        // Para reuniões: mostra horário
        time = new Date(meeting.data_hora).toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      meetingItem.innerHTML += `
        <span class="calendar-meeting-time">${time}</span>
        <span class="calendar-meeting-title" title="${meeting.titulo}">${meeting.titulo}</span>
      `;
      
      meetingItem.onclick = (e) => {
        e.stopPropagation();
        showMeetingDetails(meeting);
      };
      
      meetingsContainer.appendChild(meetingItem);
    });
    
    // Contar total de itens restantes
    const remainingHolidays = Math.max(0, dayHolidays.length - 1);
    const remainingBirthdays = Math.max(0, dayBirthdays.length - 2);
    const remainingMeetings = Math.max(0, dayMeetings.length - maxMeetings);
    const totalRemaining = remainingHolidays + remainingBirthdays + remainingMeetings;
    
    if (totalRemaining > 0) {
      const moreItem = document.createElement('div');
      moreItem.className = 'calendar-meeting-more';
      moreItem.textContent = `+${totalRemaining} mais`;
      moreItem.onclick = (e) => {
        e.stopPropagation();
        showAllDayEvents(dateStr, dayMeetings, dayBirthdays, dayHolidays);
      };
      meetingsContainer.appendChild(moreItem);
    }
    
    dayElement.appendChild(meetingsContainer);
  }
  
  // Clique no dia inteiro abre o modal com todos os eventos
  dayElement.onclick = () => {
    if (hasContent) {
      showAllDayEvents(dateStr, dayMeetings, dayBirthdays, dayHolidays);
    }
  };
  
  return dayElement;
}

// ==================== 🔧 CORREÇÃO - getMeetingsForDate ====================
function getMeetingsForDate(dateStr) {
  // Garante que allMeetings é um array
  if (!Array.isArray(allMeetings)) {
    console.warn('⚠️ allMeetings não é um array:', allMeetings);
    return [];
  }

  return allMeetings.filter(meeting => {
    if (!meeting) return false;
    
    // ==================== 🆕 CORREÇÃO DE TIMEZONE ====================
    // Para eventos (têm data_inicio e data_fim)
    if (meeting.tipo_item === 'evento' && meeting.data_inicio && meeting.data_fim) {
      // Extrai APENAS a parte da data (YYYY-MM-DD) sem conversão de timezone
      const dataInicio = extractDateOnly(meeting.data_inicio);
      const dataFim = extractDateOnly(meeting.data_fim);
      
      // Comparação direta de strings YYYY-MM-DD
      return dateStr >= dataInicio && dateStr <= dataFim;
    }
    
    // Para reuniões (têm data_hora)
    if (meeting.data_hora) {
      const meetingDate = extractDateOnly(meeting.data_hora);
      return meetingDate === dateStr;
    }
    
    return false;
  }).sort((a, b) => {
    // Usa a mesma função de extração para ordenação
    const dateA = new Date(extractDateOnly(a.data_hora || a.data_inicio) + 'T00:00:00');
    const dateB = new Date(extractDateOnly(b.data_hora || b.data_inicio) + 'T00:00:00');
    return dateA - dateB;
  });
}

function extractDateOnly(dateString) {
  if (!dateString) return '';
  
  // Remove espaços extras
  dateString = dateString.trim();
  
  // Trata diferentes formatos
  
  // Formato: "2024-12-11 14:30:00" ou "2024-12-11T14:30:00"
  if (dateString.includes(' ') || dateString.includes('T')) {
    return dateString.split(/[\sT]/)[0]; // Retorna "2024-12-11"
  }
  
  // Formato: "2024-12-11" (já está correto)
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return dateString;
  }
  
  // Formato ISO completo: "2024-12-11T14:30:00.000Z"
  if (dateString.includes('Z') || dateString.includes('+') || dateString.includes('-', 10)) {
    return dateString.split('T')[0];
  }
  
  // Fallback: tenta parsear normalmente
  try {
    const date = new Date(dateString);
    // Usa UTC para evitar conversão de timezone
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch (error) {
    console.error('Erro ao extrair data:', dateString, error);
    return '';
  }
}

function getBirthdaysForDate(month, day) {
  return allBirthdays.filter(birthday => {
    if (!birthday.data_aniversario) return false;
    
    let birthdayMonth, birthdayDay;
    
    // Tenta parsear diferentes formatos
    if (birthday.data_aniversario.includes('-')) {
      // Formato YYYY-MM-DD ou MM-DD
      const parts = birthday.data_aniversario.split('-');
      if (parts.length === 3) {
        birthdayMonth = parseInt(parts[1]);
        birthdayDay = parseInt(parts[2]);
      } else if (parts.length === 2) {
        birthdayMonth = parseInt(parts[0]);
        birthdayDay = parseInt(parts[1]);
      }
    } else if (birthday.data_aniversario.includes('/')) {
      // Formato DD/MM/YYYY ou DD/MM
      const parts = birthday.data_aniversario.split('/');
      birthdayDay = parseInt(parts[0]);
      birthdayMonth = parseInt(parts[1]);
    }
    
    return birthdayMonth === month && birthdayDay === day;
  }).sort((a, b) => a.nome.localeCompare(b.nome));
}

// ========== MODAL DE FERIADO COM DESCRIÇÃO ==========
function showHolidayDetails(holiday) {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.display = 'flex';
  
  // Determinar cor com base no tipo de feriado
  let bgColor = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
  let accentColor = '#f59e0b';
  let borderColor = '#f59e0b';
  
  if (holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd) {
    bgColor = 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)';
    accentColor = '#ec4899';
    borderColor = '#ec4899';
  }
  
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-calendar-check"></i>
          ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? 'Período de Carnaval' : 'Feriado'}
        </h2>
        <button class="close-btn" onclick="this.closest('.modal').remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div style="background: ${bgColor}; padding: 32px; border-radius: 16px; margin-bottom: 24px; text-align: center; color: white;">
          <div style="font-size: 64px; margin-bottom: 16px;">${holiday.icon}</div>
          <h3 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
            ${holiday.name}
          </h3>
          <div style="font-size: 14px; opacity: 0.9;">
            ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? 'Celebração Cultural Brasileira' : 'Feriado Nacional Brasileiro'}
          </div>
        </div>
        
        <div style="background: #f3f4f6; padding: 20px; border-radius: 12px; margin-bottom: 24px; border-left: 4px solid ${accentColor};">
          <h4 style="color: #1f2937; font-weight: 600; margin-top: 0; margin-bottom: 12px;">
            <i class="fas fa-info-circle" style="color: ${accentColor}; margin-right: 8px;"></i>
            Sobre este dia
          </h4>
          <p style="color: #4b5563; font-size: 15px; line-height: 1.6; margin: 0;">
            ${holiday.description}
          </p>
        </div>
        
        <div style="text-align: center; padding: 24px; background: ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? '#fce7f3' : '#fef3c7'}; border-radius: 12px; border-left: 4px solid ${accentColor};">
          <i class="fas ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? 'fa-music' : 'fa-calendar'}" style="color: ${accentColor}; margin-right: 8px;"></i>
          <span style="color: ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? '#831843' : '#92400e'}; font-weight: 500;">
            ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? 'Dia festivo - Celebração cultural' : 'Dia não útil - Não há expediente'}
          </span>
        </div>
      </div>
    </div>
  `;
  
  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
  
  document.body.appendChild(modal);
}

function showBirthdayDetails(birthday) {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.display = 'flex';
  
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-birthday-cake"></i>
          Aniversário
        </h2>
        <button class="close-btn" onclick="this.closest('.modal').remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div style="background: linear-gradient(135deg, #ff6b9d 0%, #c06c84 100%); padding: 32px; border-radius: 16px; margin-bottom: 24px; text-align: center; color: white;">
          <div style="font-size: 64px; margin-bottom: 16px;">🎂</div>
          <h3 style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
            ${birthday.nome}
          </h3>
          <div style="font-size: 18px; opacity: 0.9;">
            ${birthday.data_aniversario}
          </div>
        </div>
        
        <div style="display: grid; gap: 16px;">
          ${birthday.telefone ? `
            <div style="display: flex; align-items: center; gap: 12px; padding: 16px; background: #f8f9fa; border-radius: 12px;">
              <i class="fas fa-phone" style="color: #667eea; font-size: 20px; width: 24px;"></i>
              <div>
                <div style="font-size: 12px; color: #6b7280; font-weight: 600;">TELEFONE</div>
                <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${birthday.telefone}</div>
              </div>
            </div>
          ` : ''}
          
          ${birthday.email ? `
            <div style="display: flex; align-items: center; gap: 12px; padding: 16px; background: #f8f9fa; border-radius: 12px;">
              <i class="fas fa-envelope" style="color: #667eea; font-size: 20px; width: 24px;"></i>
              <div>
                <div style="font-size: 12px; color: #6b7280; font-weight: 600;">EMAIL</div>
                <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${birthday.email}</div>
              </div>
            </div>
          ` : ''}
          
          ${birthday.empresa ? `
            <div style="display: flex; align-items: center; gap: 12px; padding: 16px; background: #f8f9fa; border-radius: 12px;">
              <i class="fas fa-building" style="color: #667eea; font-size: 20px; width: 24px;"></i>
              <div>
                <div style="font-size: 12px; color: #6b7280; font-weight: 600;">EMPRESA</div>
                <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${birthday.empresa}</div>
              </div>
            </div>
          ` : ''}
        </div>
        
        <div style="text-align: center; padding: 16px; background: #fff4e6; border-radius: 12px; margin-top: 24px;">
          <i class="fas fa-gift" style="color: #ff6b9d; margin-right: 8px;"></i>
          <span style="color: #6b7280; font-size: 14px;">Dados do arquivo: <strong>2D consultores</strong></span>
        </div>
      </div>
    </div>
  `;
  
  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
  
  document.body.appendChild(modal);
}

function showMeetingDetails(meeting) {
  // Detecta se é evento ou reunião
  const isEvento = meeting.tipo_item === 'evento';
  
  // Formata datas
  let formatDate, time;
  
  if (isEvento) {
    // Eventos têm data_inicio e data_fim
    const dataInicio = new Date(meeting.data_inicio);
    const dataFim = new Date(meeting.data_fim);
    
    formatDate = `${dataInicio.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      weekday: 'long'
    })} até ${dataFim.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      weekday: 'long'
    })}`;
    
    time = `${dataInicio.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })} - ${dataFim.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })}`;
    
  } else {
    // Reuniões têm data_hora
    formatDate = new Date(meeting.data_hora).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      weekday: 'long'
    });
    
    time = new Date(meeting.data_hora).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  // Status para reuniões
  let statusText = '', statusColor = '', statusIcon = '';
  
  if (!isEvento) {
    statusText = meeting.confirmation_status === 'confirmed' ? 'Confirmada' : 
                    meeting.confirmation_status === 'declined' ? 'Recusada' : 'Pendente';
    statusColor = meeting.confirmation_status === 'confirmed' ? '#10b981' : 
                     meeting.confirmation_status === 'declined' ? '#ef4444' : '#f59e0b';
    statusIcon = meeting.confirmation_status === 'confirmed' ? 'fa-check-circle' : 
                    meeting.confirmation_status === 'declined' ? 'fa-times-circle' : 'fa-clock';
  }
  
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.display = 'flex';
  
  // Ícones de tipo de evento
  const eventoIcons = {
    'viagem': '✈️',
    'feira': '🏢',
    'conferencia': '🎤',
    'treinamento': '📚',
    'evento_interno': '🎉',
    'outro': '📅'
  };
  
  const eventoIcon = isEvento ? (eventoIcons[meeting.tipo] || '📅') : '📋';
  
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-info-circle"></i>
          ${isEvento ? 'Detalhes do Evento' : 'Detalhes da Reunião'}
        </h2>
        <button class="close-btn" onclick="this.closest('.modal').remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 24px; border-radius: 16px; margin-bottom: 24px;">
          <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
            <div style="flex-shrink: 0; font-size: 48px;">
              ${eventoIcon}
            </div>
            <div style="flex: 1;">
              <h3 style="font-size: 24px; font-weight: 700; color: #1a1a1a; margin-bottom: 8px;">
                ${meeting.titulo}
              </h3>
              ${!isEvento ? `
                <div style="display: inline-block; background: ${statusColor}; color: white; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;">
                  ${statusText}
                </div>
              ` : `
                <div style="display: inline-block; background: #667eea; color: white; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;">
                  ${meeting.tipo ? meeting.tipo.replace('_', ' ').toUpperCase() : 'EVENTO'}
                </div>
              `}
            </div>
          </div>
          
          <div style="display: grid; gap: 16px; margin-top: 24px;">
            <div style="display: flex; align-items: center; gap: 12px;">
              <i class="fas fa-calendar-alt" style="color: #667eea; font-size: 20px; width: 24px;"></i>
              <div>
                <div style="font-size: 12px; color: #6b7280; font-weight: 600;">DATA</div>
                <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${formatDate}</div>
              </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 12px;">
              <i class="fas fa-clock" style="color: #667eea; font-size: 20px; width: 24px;"></i>
              <div>
                <div style="font-size: 12px; color: #6b7280; font-weight: 600;">HORÁRIO</div>
                <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${time}</div>
              </div>
            </div>
            
            ${isEvento ? `
              ${meeting.local ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-map-marker-alt" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">LOCAL</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.local}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.participantes ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-users" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">PARTICIPANTES</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.participantes}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.descricao ? `
                <div style="display: flex; align-items: start; gap: 12px;">
                  <i class="fas fa-align-left" style="color: #667eea; font-size: 20px; width: 24px; margin-top: 2px;"></i>
                  <div style="flex: 1;">
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600; margin-bottom: 4px;">DESCRIÇÃO</div>
                    <div style="font-size: 14px; color: #4b5563; line-height: 1.6;">${meeting.descricao}</div>
                  </div>
                </div>
              ` : ''}
            ` : `
              <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-user" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                <div>
                  <div style="font-size: 12px; color: #6b7280; font-weight: 600;">CONVIDADO</div>
                  <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.convidado}</div>
                </div>
              </div>
              
              ${meeting.nome_cliente ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-building" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">EMPRESA</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.nome_cliente}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.assunto ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-file-alt" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">ASSUNTO</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.assunto}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.telefone_cliente ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-phone" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">TELEFONE</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.telefone_cliente}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.local_reuniao ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-map-marker-alt" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">LOCAL</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">${meeting.local_reuniao}</div>
                  </div>
                </div>
              ` : ''}
              
              ${meeting.link ? `
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-link" style="color: #667eea; font-size: 20px; width: 24px;"></i>
                  <div>
                    <div style="font-size: 12px; color: #6b7280; font-weight: 600;">LINK</div>
                    <div style="font-size: 16px; color: #1a1a1a; font-weight: 700;">
                      <a href="${meeting.link}" target="_blank" style="color: #667eea; text-decoration: none;">
                        ${meeting.link}
                      </a>
                    </div>
                  </div>
                </div>
              ` : ''}
            `}
          </div>
        </div>
        
        ${isEvento ? `
          <!-- BOTÕES DE AÇÃO PARA EVENTOS -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
            <button 
              onclick="editarEvento(${meeting.id})" 
              style="display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.3s ease;"
              onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 16px rgba(102, 126, 234, 0.4)';"
              onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
            >
              <i class="fas fa-edit"></i> Editar Evento
            </button>
            
            <button 
              onclick="excluirEvento(${meeting.id}, '${meeting.titulo.replace(/'/g, "\\'")}'); event.stopPropagation();" 
              style="display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; border: none; border-radius: 10px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.3s ease;"
              onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 16px rgba(239, 68, 68, 0.4)';"
              onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
            >
              <i class="fas fa-trash"></i> Excluir Evento
            </button>
          </div>
        ` : ''}
        
        <div style="text-align: center; padding: 16px; background: #f8f9fa; border-radius: 12px;">
          <i class="fas fa-info-circle" style="color: #667eea; margin-right: 8px;"></i>
          <span style="color: #6b7280; font-size: 14px;">
            ${isEvento ? 'Evento cadastrado no sistema' : 'Modo visualização - Para editar, volte para a página principal'}
          </span>
        </div>
      </div>
    </div>
  `;
  
  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
  
  document.body.appendChild(modal);
}

// ========== ATUALIZAR showAllDayEvents PARA INCLUIR FERIADOS ==========
function showAllDayEvents(dateStr, meetings, birthdays, holidays = []) {
  const formatDate = new Date(dateStr + 'T12:00:00').toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    weekday: 'long'
  });
  
  const totalEvents = meetings.length + birthdays.length + holidays.length;
  
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.display = 'flex';
  
  // ========== SECTION FERIADOS ==========
  let holidaysHTML = '';
  if (holidays.length > 0) {
    holidaysHTML = `
      <div style="margin-bottom: 24px;">
        <h3 style="display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px;">
          <i class="fas fa-calendar-check" style="color: #f59e0b;"></i>
          Feriados e Datas Especiais (${holidays.length})
        </h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${holidays.map(holiday => {
            let accentColor = '#f59e0b';
            let bgColor = 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
            let borderColor = '#f59e0b';
            
            if (holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd) {
              accentColor = '#ec4899';
              bgColor = 'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)';
              borderColor = '#ec4899';
            }
            
            return `
              <div class="meeting-list-item" onclick="event.stopPropagation(); showHolidayFromList(${JSON.stringify(holiday).replace(/"/g, '&quot;')});" style="cursor: pointer; background: ${bgColor}; border-left: 4px solid ${borderColor};">
                <div style="display: flex; align-items: center; gap: 15px;">
                  <div style="flex-shrink: 0; display: flex; flex-direction: column; align-items: center; padding: 12px; background: ${accentColor}15; border-radius: 12px; min-width: 80px;">
                    <div style="font-size: 32px;">${holiday.icon}</div>
                  </div>
                  <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                      <div style="font-weight: 700; font-size: 18px; color: #1a1a1a;">
                        ${holiday.name}
                      </div>
                      <div style="display: inline-block; background: ${accentColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                        ${holiday.isCarnavalStart || holiday.isCarnavalPart || holiday.isCarnavalEnd ? 'Carnaval' : 'Feriado'}
                      </div>
                    </div>
                    <div style="color: #6b7280; font-size: 13px;">
                      <i class="fas fa-book" style="margin-right: 6px;"></i>${holiday.description.substring(0, 80)}...
                    </div>
                  </div>
                  <div style="flex-shrink: 0;">
                    <i class="fas fa-chevron-right" style="color: ${borderColor}; font-size: 16px;"></i>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }
  
  // ========== SECTION ANIVERSÁRIOS ==========
  let birthdaysHTML = '';
  if (birthdays.length > 0) {
    birthdaysHTML = `
      <div style="margin-bottom: 24px;">
        <h3 style="display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px;">
          <i class="fas fa-birthday-cake" style="color: #ff6b9d;"></i>
          Aniversários (${birthdays.length})
        </h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${birthdays.map(birthday => `
            <div class="meeting-list-item" onclick="event.stopPropagation(); showBirthdayFromList(${JSON.stringify(birthday).replace(/"/g, '&quot;')});" style="cursor: pointer; background: linear-gradient(135deg, #fff5f8 0%, #ffe5ee 100%); border-left: 4px solid #ff6b9d;">
              <div style="display: flex; align-items: center; gap: 15px;">
                <div style="flex-shrink: 0; display: flex; flex-direction: column; align-items: center; padding: 12px; background: #ff6b9d15; border-radius: 12px; min-width: 80px;">
                  <div style="font-size: 32px;">🎂</div>
                </div>
                <div style="flex: 1;">
                  <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 18px; color: #1a1a1a;">
                      ${birthday.nome}
                    </div>
                    <div style="display: inline-block; background: #ff6b9d; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                      Aniversário
                    </div>
                  </div>
                  <div style="color: #6b7280; font-size: 14px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                    ${birthday.telefone ? `<span><i class="fas fa-phone" style="margin-right: 6px;"></i>${birthday.telefone}</span>` : ''}
                    ${birthday.empresa ? `<span><i class="fas fa-building" style="margin-right: 6px;"></i>${birthday.empresa}</span>` : ''}
                  </div>
                </div>
                <div style="flex-shrink: 0;">
                  <i class="fas fa-chevron-right" style="color: #ff6b9d; font-size: 16px;"></i>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
  
  // ========== SECTION REUNIÕES E EVENTOS ==========
  let meetingsHTML = '';
  if (meetings.length > 0) {
    meetingsHTML = `
      <div>
        <h3 style="display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px;">
          <i class="fas fa-calendar-check" style="color: #667eea;"></i>
          Reuniões e Eventos (${meetings.length})
        </h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${meetings.map(meeting => {
            const isEvento = meeting.tipo_item === 'evento';
            
            let time = '';
            if (isEvento) {
              const eventoIcons = {
                'viagem': '✈️',
                'feira': '🏢',
                'conferencia': '🎤',
                'treinamento': '📚',
                'evento_interno': '🎉',
                'outro': '📅'
              };
              time = eventoIcons[meeting.tipo] || '📅';
            } else {
              time = new Date(meeting.data_hora).toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit'
              });
            }
            
            let statusColor = '#667eea';
            let statusIcon = 'fa-calendar';
            let statusText = 'Evento';
            
            if (!isEvento) {
              statusColor = meeting.confirmation_status === 'confirmed' ? '#10b981' : 
                             meeting.confirmation_status === 'declined' ? '#ef4444' : '#f59e0b';
              statusIcon = meeting.confirmation_status === 'confirmed' ? 'fa-check-circle' : 
                            meeting.confirmation_status === 'declined' ? 'fa-times-circle' : 'fa-clock';
              statusText = meeting.confirmation_status === 'confirmed' ? 'Confirmada' : 
                            meeting.confirmation_status === 'declined' ? 'Recusada' : 'Pendente';
            }
            
            return `
              <div class="meeting-list-item" onclick="event.stopPropagation(); showMeetingFromList(${JSON.stringify(meeting).replace(/"/g, '&quot;')});" style="cursor: pointer; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; gap: 15px;">
                  <div style="flex-shrink: 0; display: flex; flex-direction: column; align-items: center; padding: 12px; background: ${statusColor}15; border-radius: 12px; min-width: 80px;">
                    ${isEvento ? `
                      <div style="font-size: 32px;">${time}</div>
                    ` : `
                      <i class="fas fa-clock" style="color: ${statusColor}; font-size: 20px; margin-bottom: 4px;"></i>
                      <div style="font-weight: 700; font-size: 18px; color: ${statusColor};">
                        ${time}
                      </div>
                    `}
                  </div>
                  <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                      <i class="fas ${statusIcon}" style="color: ${statusColor}; font-size: 20px;"></i>
                      <div style="font-weight: 700; font-size: 18px; color: #1a1a1a;">
                        ${meeting.titulo}
                      </div>
                      <div style="display: inline-block; background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                        ${statusText}
                      </div>
                    </div>
                    <div style="color: #6b7280; font-size: 14px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                      ${!isEvento ? `
                        <span><i class="fas fa-user" style="margin-right: 6px;"></i>${meeting.convidado}</span>
                        ${meeting.nome_cliente ? `<span><i class="fas fa-building" style="margin-right: 6px;"></i>${meeting.nome_cliente}</span>` : ''}
                        ${meeting.assunto ? `<span><i class="fas fa-file-alt" style="margin-right: 6px;"></i>${meeting.assunto}</span>` : ''}
                        ${meeting.local_reuniao ? `<span><i class="fas fa-map-marker-alt" style="margin-right: 6px;"></i>${meeting.local_reuniao}</span>` : ''}
                      ` : `
                        ${meeting.local ? `<span><i class="fas fa-map-marker-alt" style="margin-right: 6px;"></i>${meeting.local}</span>` : ''}
                        ${meeting.participantes ? `<span><i class="fas fa-users" style="margin-right: 6px;"></i>${meeting.participantes}</span>` : ''}
                      `}
                    </div>
                  </div>
                  <div style="flex-shrink: 0;">
                    <i class="fas fa-chevron-right" style="color: #d1d5db; font-size: 16px;"></i>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }
  
  modal.innerHTML = `
    <div class="modal-content" style="max-width: 800px;">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-calendar-day"></i>
          ${formatDate}
        </h2>
        <button class="close-btn" onclick="this.closest('.modal').remove()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div style="margin-bottom: 20px; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; text-align: center;">
          <i class="fas fa-calendar-alt" style="font-size: 32px; margin-bottom: 8px;"></i>
          <h3 style="margin: 0; font-size: 20px; font-weight: 700;">${totalEvents} Eventos Hoje</h3>
          <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">
            ${holidays.length > 0 ? `${holidays.length} feriado${holidays.length > 1 ? 's' : ''}` : ''}
            ${holidays.length > 0 && birthdays.length > 0 ? ' • ' : ''}
            ${birthdays.length > 0 ? `${birthdays.length} aniversário${birthdays.length > 1 ? 's' : ''}` : ''}
            ${(holidays.length > 0 || birthdays.length > 0) && meetings.length > 0 ? ' • ' : ''}
            ${meetings.length > 0 ? `${meetings.length} reuniã${meetings.length > 1 ? 'ões' : 'o'}` : ''}
          </p>
        </div>
        
        ${holidaysHTML}
        ${birthdaysHTML}
        ${meetingsHTML}
        
        ${totalEvents === 0 ? `
          <div style="text-align: center; padding: 48px 24px; color: #9ca3af;">
            <i class="fas fa-calendar" style="font-size: 64px; margin-bottom: 16px; opacity: 0.3;"></i>
            <p style="font-size: 16px; margin: 0;">Nenhum evento agendado para este dia</p>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
  
  document.body.appendChild(modal);
}

function showMeetingFromList(meeting) {
  const currentModal = document.querySelector('.modal');
  if (currentModal) {
    currentModal.remove();
  }
  
  setTimeout(() => {
    showMeetingDetails(meeting);
  }, 100);
}

function showBirthdayFromList(birthday) {
  const currentModal = document.querySelector('.modal');
  if (currentModal) {
    currentModal.remove();
  }
  
  setTimeout(() => {
    showBirthdayDetails(birthday);
  }, 100);
}

function showHolidayFromList(holiday) {
  const currentModal = document.querySelector('.modal');
  if (currentModal) {
    currentModal.remove();
  }
  
  setTimeout(() => {
    showHolidayDetails(holiday);
  }, 100);
}

function previousMonth() {
  currentDate.setMonth(currentDate.getMonth() - 1);
  loadHolidays();
  renderCalendar();
}

function nextMonth() {
  currentDate.setMonth(currentDate.getMonth() + 1);
  loadHolidays();
  renderCalendar();
}

function goToToday() {
  currentDate = new Date();
  loadHolidays();
  renderCalendar();
}

window.addEventListener('DOMContentLoaded', initCalendar);

// ==================== 🆕 FUNÇÕES DE EDIÇÃO E EXCLUSÃO DE EVENTOS ====================

/**
 * Editar evento do calendário
 */
async function editarEvento(eventoId) {
  try {
    // 🔧 CORREÇÃO: URL correta da API
    const response = await fetch(`/api/eventos/get/${eventoId}`);
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'Erro ao carregar evento');
    }
    
    // Salva no sessionStorage para página principal recuperar
    sessionStorage.setItem('editando_evento', JSON.stringify({
      id: eventoId,
      ...data.evento
    }));
    
    // Redireciona para página principal (onde está modal de eventos)
    window.location.href = `/`;
    
  } catch (error) {
    console.error('❌ Erro ao editar evento:', error);
    alert('Erro ao carregar dados do evento. Tente novamente.');
  }
}

/**
 * Excluir evento do calendário
 */
async function excluirEvento(eventoId, titulo) {
  // Confirmação com usuário
  const confirmar = confirm(
    `⚠️ ATENÇÃO: Deseja realmente excluir o evento?\n\n` +
    `📅 ${titulo}\n\n` +
    `Esta ação não pode ser desfeita!`
  );
  
  if (!confirmar) return;
  
  try {
    const response = await fetch(`/api/eventos/excluir/${eventoId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Fecha modal
      const modal = document.querySelector('.modal');
      if (modal) modal.remove();
      
      // Mostra sucesso
      showSuccessNotification('✅ Evento excluído com sucesso!');
      
      // Recarrega calendário
      await loadMeetings();
      renderCalendar();
      
    } else {
      throw new Error(data.message || 'Erro ao excluir evento');
    }
    
  } catch (error) {
    console.error('❌ Erro ao excluir evento:', error);
    alert('Erro ao excluir evento. Tente novamente.');
  }
}

/**
 * Mostra notificação de sucesso
 */
function showSuccessNotification(message) {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    z-index: 10000;
    font-weight: 600;
    animation: slideIn 0.3s ease-out;
  `;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Remove após 3 segundos
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Adiciona animações CSS
if (!document.getElementById('calendar-animations')) {
  const style = document.createElement('style');
  style.id = 'calendar-animations';
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
    
    /* Estilo especial para eventos no calendário */
    .calendar-meeting-item.evento-item {
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      border-left: 3px solid #f59e0b;
    }
    
    .calendar-meeting-item.evento-item:hover {
      background: linear-gradient(135deg, #fde68a 0%, #fbbf24 100%);
      transform: translateX(2px);
    }
    
    .calendar-meeting-item.evento-item .calendar-meeting-time {
      font-size: 14px; /* Ícone um pouco maior */
    }
  `;
  document.head.appendChild(style);
}