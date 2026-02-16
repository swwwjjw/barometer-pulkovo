import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell
} from 'recharts'
import './App.css'

const CHART_COLORS = {
  // Основные цвета для мультиколорных чартов
  palette: [
    '#3b82f6', // --chart-color-1: Blue 500
    '#22d3ee', // --chart-color-2: Cyan 400
    '#a78bfa', // --chart-color-3: Violet 400
    '#f472b6', // --chart-color-4: Pink 400
    '#fbbf24'  // --chart-color-5: Amber 400
  ],
  // Акцентные цвета для одноцветных чартов
  primary: '#3b82f6',    // --accent-primary
  secondary: '#60a5fa',  // --accent-secondary
  // Цвета сеток и осей
  axis: '#94a3b8',       // --text-muted
  grid: '#334155'        // --bg-tertiary
};

// Сопоставление ключевых слов с бэкенда и отображаемых названий
const ROLE_DISPLAY_NAMES = {
  'грузчик нагрузки': 'Грузчик на склад',
  'аналитик данных SQL': 'Аналитик данных',
  'ml engineer': 'ML инженер',
  'машинист катка': 'Машинист катка',
  'руководитель склада OR NAME:(инженер склада)': 'Инженер склада',
  'фельдшер помощь': 'Фельдшер / фельдшер скорой медицинской помощи',
  'обслуживание воздушных судов': 'Специалист по обслуживанию ВС',
  'мойщик посуды': 'Мойщик-уборщик',
  'осмотр медицинской': 'Медицинская сестра/медицинский брат',
  'системный виртуализация': 'Системный инженер',
  'склад комплектовщик': 'Инспектор Перронного Контроля',
  'кинолог': 'Кинолог',
  'инженер холодильного': 'Инженер холодильных установок',
  'гбр охрана': 'Инспектор Группы Быстрого Реагирования',
  'бариста выпечка': 'Агент (универсальный сотрудник) магазина',
  'отчетность пекарня': 'Координатор (администратор) магазина',
  'закупки булочная': 'Ведущий специалист магазина',
  'управляющий кафе': 'Директор (управляющий) магазина',
  'товаровед качество': 'Товаровед магазина'
};

// Надбавки к зарплате для каждой роли (в рублях)
const TEAM_PROJECT_SALARY = {
  'грузчик нагрузки': 39494,
  'аналитик данных SQL': 0,
  'ml engineer': 0,
  'машинист катка': 0,
  'руководитель склада OR NAME:(инженер склада)': 0,
  'фельдшер помощь': 0,
  'обслуживание воздушных судов': 30688,
  'мойщик посуды': 0,
  'осмотр медицинской': 0,
  'системный виртуализация': 0,
  'склад комплектовщик': 25800,
  'кинолог': 0,
  'инженер холодильного': 0,
  'гбр охрана': 0,
  'бариста выпечка': 0,
  'отчетность пекарня': 0,
  'закупки булочная': 0,
  'управляющий кафе': 0,
  'товаровед качество': 0
};

// Получить отображаемое название для роли по ключевым словам
const getRoleDisplayName = (keywords) => {
  return ROLE_DISPLAY_NAMES[keywords] || keywords;
};

function App() {
  // Состояние вкладки - определяем из пути URL
  const [activeTab, setActiveTab] = useState(() => {
    const path = window.location.pathname;
    if (path.startsWith('/b1')) {
      return 'b1';
    }
    return 'hh';
  });
  
  // Состояние для вкладки HH
  const [groups, setGroups] = useState([])
  const [selectedGroupId, setSelectedGroupId] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [overallStats, setOverallStats] = useState(null)
  const [teamProjectActive, setTeamProjectActive] = useState(false)
  
  // Состояние для вкладки B1
  const [b1Blocks, setB1Blocks] = useState([])
  const [selectedBlockIndex, setSelectedBlockIndex] = useState(null)
  const [selectedBlock, setSelectedBlock] = useState(null)
  const [b1Loading, setB1Loading] = useState(false)
  const [b1Error, setB1Error] = useState(null)

  // Обновление URL при смене вкладки
  useEffect(() => {
    const path = activeTab === 'b1' ? '/b1' : '/';
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
  }, [activeTab]);

  // Загрузка данных HH при активной вкладке hh
  useEffect(() => {
    if (activeTab !== 'hh') return;
    axios.get('/api/groups')
      .then(res => {
        setGroups(res.data)
        if (res.data.length > 0) {
          const firstGroupId = res.data[0].id
          setSelectedGroupId(firstGroupId)
          fetchStats(firstGroupId)
        }
      })
      .catch(err => setError("Не удалось загрузить группы"))
    
    axios.get('/api/overall-stats')
      .then(res => {
        setOverallStats(res.data)
      })
      .catch(err => console.error("Не удалось загрузить общую статистику"))
  }, [activeTab])
  
  // Загрузка данных B1 при активной вкладке b1
  useEffect(() => {
    if (activeTab !== 'b1') return;
    
    setB1Loading(true);
    setB1Error(null);
    
    axios.get('/api/b1/blocks')
      .then(res => {
        setB1Blocks(res.data);
        if (res.data.length > 0) {
          setSelectedBlockIndex(0);
          fetchBlockDetails(0);
        }
        setB1Loading(false);
      })
      .catch(err => {
        setB1Error("Ошибка загрузки данных Б1");
        setB1Loading(false);
      });
  }, [activeTab])

  const fetchBlockDetails = (blockIndex) => {
    setB1Loading(true);
    axios.get(`/api/b1/blocks/${blockIndex}`)
      .then(res => {
        setSelectedBlock(res.data);
        setB1Loading(false);
      })
      .catch(err => {
        setB1Error("Ошибка загрузки блока");
        setB1Loading(false);
      });
  }
  
  const handleBlockChange = (e) => {
    const index = parseInt(e.target.value);
    setSelectedBlockIndex(index);
    fetchBlockDetails(index);
  }

  const fetchStats = (groupId) => {
    setLoading(true)
    setError(null)
    axios.get(`/api/stats/${groupId}`)
      .then(res => {
        if (res.data.error) {
          setError(res.data.error)
          setStats(null)
        } else {
          setStats(res.data)
        }
        setLoading(false)
      })
      .catch(err => {
        setError("Не удалось загрузить статистику")
        setLoading(false)
      })
  }

  const handleGroupChange = (e) => {
    const groupId = e.target.value
    setSelectedGroupId(groupId)
    fetchStats(groupId)
  }

  const toggleTeamProject = () => {
    setTeamProjectActive(!teamProjectActive)
  }

  const getTeamProjectBonus = () => {
    if (!teamProjectActive || !stats) return 0
    const currentKeywords = stats.keywords
    return TEAM_PROJECT_SALARY[currentKeywords] || 0
  }

  const renderB1Content = () => (
    <>
      <div className="header">
        <h1>Обзор зарплат Б1</h1>
        <div className="controls">
          <select 
            value={selectedBlockIndex ?? ''} 
            onChange={handleBlockChange}
            disabled={b1Loading}
          >
            {b1Blocks.map((block, index) => (
              <option key={index} value={index}>
                {block.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      {b1Loading && <div className="loading">Загрузка...</div>}
      {b1Error && <div className="error">{b1Error}</div>}
      
      {!b1Loading && selectedBlock && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Среднее</h3>
              <div className="value">{Math.round(selectedBlock.stats.avg).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Медиана</h3>
              <div className="value">{Math.round(selectedBlock.stats.median).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Минимум</h3>
              <div className="value">{Math.round(selectedBlock.stats.min).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Максимум</h3>
              <div className="value">{Math.round(selectedBlock.stats.max).toLocaleString()}</div>
            </div>
          </div>
          
          <div className="b1-positions-card">
            <h3>Должности в блоке "{selectedBlock.name}"</h3>
            <div className="b1-positions-table">
              <div className="b1-table-header">
                <div className="b1-col-name">Должность</div>
                <div className="b1-col-salary">Зарплата</div>
              </div>
              {selectedBlock.positions.map((position, idx) => (
                <div key={idx} className="b1-table-row">
                  <div className="b1-col-name">{position.name}</div>
                  <div className="b1-col-salary">{Math.round(position.salary).toLocaleString()} ₽</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );

  return (
    <div className="container">
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'hh' ? 'active' : ''}`}
          onClick={() => setActiveTab('hh')}
        >
          HH
        </button>
        <button 
          className={`tab-btn ${activeTab === 'b1' ? 'active' : ''}`}
          onClick={() => setActiveTab('b1')}
        >
          Б1
        </button>
      </div>
      
      {activeTab === 'b1' ? renderB1Content() : (
      <>
      <div className="header">
        <h1>Барометр вакансий ВВСС</h1>
        <div className="controls">
          <select value={selectedGroupId || ''} onChange={handleGroupChange}>
            {groups.map((group) => (
              <option key={group.id} value={group.id}>
                {getRoleDisplayName(group.keywords)}
              </option>
            ))}
          </select>
          {stats && stats.metrics && (
            <div className="vacancy-count">
              Всего вакансий в группе: <span>{stats.metrics.count}</span>
            </div>
          )}
        </div>
      </div>

      {!loading && stats && stats.metrics && stats.comparison && (
        <div className="market-card">
          <h3>Сравнение с рынком по заработной плате</h3>
          <div className="market-card-header">
            <button 
              className={`team-project-btn ${teamProjectActive ? 'active' : ''}`}
              onClick={toggleTeamProject}
            >
              С проектом "Мы команда" {teamProjectActive ? '✓' : ''}
            </button>
          </div>
          <div className="market-labels">
            <div className="label-below">Ниже рынка</div>
            <div className="label-in">В рынке</div>
            <div className="label-above">Выше рынка</div>
          </div>
          <div className="market-scale">
            <div 
              className="band-below" 
              style={{ width: '25%' }}
            ></div>
            <div 
              className="band-in" 
              style={{ left: '25%', width: '50%' }}
            ></div>
            <div 
              className="band-above" 
              style={{ left: '75%', width: '25%' }}
            ></div>
            {stats.comparison.pulkovo > 0 && (() => {
              const minSalary = stats.metrics.min;
              const maxSalary = stats.metrics.max;
              const teamBonus = getTeamProjectBonus();
              const pulkovoSalary = stats.comparison.pulkovo + teamBonus;
              const range = maxSalary - minSalary;
            
              const pulkovoPosition = range > 0 
                ? ((pulkovoSalary - minSalary) / range) * 100 
                : 50;
              
              const clampedPosition = Math.min(Math.max(pulkovoPosition, 2), 98);
              
              return (
                <>
                  <div 
                    className="marker-pulkovo-line" 
                    style={{ left: `${clampedPosition}%` }}
                    title={`Пулково: ${Math.round(pulkovoSalary).toLocaleString()} ₽${teamBonus > 0 ? ` (+ ${teamBonus.toLocaleString()} ₽ от проекта "Мы команда")` : ''}`}
                  ></div>
                  <div 
                    className="marker-pulkovo-label" 
                    style={{ left: `${clampedPosition}%` }}
                  >
                    {Math.round(pulkovoSalary).toLocaleString()} ₽
                  </div>
                </>
              );
            })()}
          </div>
          <div className="market-ticks">
            <div className="val-min">{Math.round(stats.metrics.min).toLocaleString()} ₽</div>
            <div className="val-p25">{Math.round((stats.metrics.max - stats.metrics.min) * 0.25 + stats.metrics.min).toLocaleString()} ₽</div>
            <div className="val-p75">{Math.round((stats.metrics.max - stats.metrics.min) * 0.75 + stats.metrics.min).toLocaleString()} ₽</div>
            <div className="val-max">{Math.round(stats.metrics.max).toLocaleString()} ₽</div>
          </div>
        </div>
      )}

      {loading && <div className="loading">Загрузка...</div>}
      
      {error && <div className="error">{error}</div>}

      {!loading && stats && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Среднее</h3>
              <div className="value">{Math.round(stats.metrics.avg).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Медиана</h3>
              <div className="value">{Math.round(stats.metrics.median).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Минимум</h3>
              <div className="value">{Math.round(stats.metrics.min).toLocaleString()}</div>
            </div>
            <div className="metric-card">
              <h3>Максимум</h3>
              <div className="value">{Math.round(stats.metrics.max).toLocaleString()}</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card chart-card-fullscreen">
              <h3>Зарплата vs Опыт</h3>
              <ResponsiveContainer width="100%" height="65%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis type="number" dataKey="salary" name="Зарплата" unit="₽" stroke={CHART_COLORS.axis} />
                  <YAxis 
                    type="number" 
                    dataKey="experience" 
                    name="Опыт" 
                    stroke={CHART_COLORS.axis}
                    domain={[0, 8]}
                    ticks={[0, 2, 4.5, 8]}
                    tickFormatter={(value) => {
                      const labels = {
                        0: 'Нет опыта',
                        2: 'От 1 года до 3 лет',
                        4.5: 'От 3 до 6 лет',
                        8: 'Более 6 лет'
                      };
                      return labels[value] || value;
                    }}
                    width={75}
                  />
                  <ZAxis type="number" dataKey="count" range={[60, 400]} name="Вакансии" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        // Подсчёт количества вакансий по работодателям для цветовой карты
                        const employerCounts = {};
                        stats.bubble_data.forEach(item => {
                          const employer = item.employer || 'Не указано';
                          employerCounts[employer] = (employerCounts[employer] || 0) + item.count;
                        });
                        const sortedEmployers = Object.entries(employerCounts)
                          .sort((a, b) => b[1] - a[1])
                          .map(([employer]) => employer);
                        const currentEmployer = data.employer || 'Не указано';
                        const employerIndex = sortedEmployers.indexOf(currentEmployer);
                        const employerColor = CHART_COLORS.palette[employerIndex % CHART_COLORS.palette.length];
                        
                        return (
                          <div className="custom-tooltip" style={{
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            padding: '12px',
                            border: '1px solid #475569',
                            borderRadius: '6px',
                            color: '#e2e8f0'
                          }}>
                            <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', fontSize: '14px', color: employerColor }}>
                              {currentEmployer}
                            </p>
                            <p style={{ margin: '4px 0', fontSize: '13px' }}>
                              <strong>Зарплата:</strong> {Math.round(data.salary).toLocaleString()} ₽
                            </p>
                            <p style={{ margin: '4px 0', fontSize: '13px' }}>
                              <strong>Опыт:</strong> {data.experience_label}
                            </p>
                            <p style={{ margin: '4px 0', fontSize: '13px' }}>
                              <strong>Вакансий:</strong> {data.count}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter 
                    name="Vacancies" 
                    data={stats.bubble_data} 
                    shape={(props) => {
                      const { cx, cy, payload } = props;
                      const radius = 10;
                      const isPulkovo = payload.employer?.trim() === 'Аэропорт Пулково (ООО Воздушные Ворота Северной Столицы)';
                      const fillColor = isPulkovo ? '#22d3ee' : '#3b82f6';
                      return (
                        <circle
                          cx={cx}
                          cy={cy}
                          r={radius}
                          fill={fillColor}
                          fillOpacity={0.8}
                          stroke={fillColor}
                          strokeWidth={1}
                        />
                      );
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
              <div className="employer-list">
                <h4 style={{ 
                  margin: '16px 0 12px 0', 
                  fontSize: '14px', 
                  fontWeight: '600', 
                  color: 'var(--text-secondary)',
                  textAlign: 'center'
                }}>
                  Работодатели в данной выборке
                </h4>
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: '8px', 
                  justifyContent: 'center',
                  maxHeight: '120px',
                  overflowY: 'auto',
                  padding: '8px'
                }}>
                  {(() => {
                    const employerCounts = {};
                    stats.bubble_data.forEach(item => {
                      const employer = item.employer || 'Не указано';
                      employerCounts[employer] = (employerCounts[employer] || 0) + item.count;
                    });
                    return Object.entries(employerCounts)
                      .sort((a, b) => b[1] - a[1])
                      .map(([employer, count], index) => (
                        <div 
                          key={index} 
                          style={{
                            backgroundColor: CHART_COLORS.palette[index % CHART_COLORS.palette.length],
                            color: 'white',
                            padding: '6px 12px',
                            borderRadius: '16px',
                            fontSize: '12px',
                            fontWeight: '500',
                            whiteSpace: 'nowrap',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                          }}
                        >
                          {employer} ({count})
                        </div>
                      ));
                  })()}
                </div>
              </div>
            </div>

            <div className="chart-card">
              <h3>Распределение опыта</h3>
              <ResponsiveContainer width="100%" height="65%">
                <PieChart>
                  <Pie
                    data={stats.experience_dist.filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius="70%"
                    fill={CHART_COLORS.primary}
                    dataKey="value"
                    animationBegin={200}
                    animationDuration={800}
                  >
                    {stats.experience_dist.filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS.palette[index % CHART_COLORS.palette.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card chart-card-fullscreen">
              <h3>Распределение зарплат</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.salary_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="range" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение по типу занятости</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.employment_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Распределение по графику работы</h3>
              <ResponsiveContainer width="100%" height="65%">
                <BarChart
                  data={stats.schedule_dist}
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} opacity={0.3} />
                  <XAxis interval="0" dataKey="name" stroke={CHART_COLORS.axis} />
                  <YAxis stroke={CHART_COLORS.axis} />
                  <Tooltip />
                  <Bar dataKey="count" fill={CHART_COLORS.primary} name="Количество" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      <div className="header">
        <h1>Общая статистика</h1>
        <div className="controls">
          {overallStats && (
            <div className="vacancy-count">
              Всего вакансий: <span>{overallStats.total_count}</span>
            </div>
          )}
        </div>
      </div>

      {overallStats && overallStats.metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Среднее</h3>
            <div className="value">{Math.round(overallStats.metrics.avg).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Медиана</h3>
            <div className="value">{Math.round(overallStats.metrics.median).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Минимум</h3>
            <div className="value">{Math.round(overallStats.metrics.min).toLocaleString()}</div>
          </div>
          <div className="metric-card">
            <h3>Максимум</h3>
            <div className="value">{Math.round(overallStats.metrics.max).toLocaleString()}</div>
          </div>
        </div>
      )}

      <div className="company-table-card">
        <h3>Зарплаты по компаниям</h3>
        <table className="company-salary-table">
          <thead>
            <tr>
              <th>Название компании</th>
              <th>ЧТС</th>
              <th>Минимальная зарплата</th>
              <th>Максимальная зарплата</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Яндекс Лавка</td><td>400</td><td>16 000</td><td>93 808</td></tr>
            <tr><td>Яндекс Еда</td><td>400</td><td>16 000</td><td>101 516</td></tr>
            <tr><td>Самокат</td><td>350</td><td>14 000</td><td>63 140</td></tr>
            <tr><td>Яндекс Крауд</td><td>350</td><td>14 000</td><td>75 440</td></tr>
            <tr><td>Т-Банк</td><td>330</td><td>13 200</td><td>65 600</td></tr>
            <tr><td>Ozon</td><td>320</td><td>12 800</td><td>106 600</td></tr>
            <tr><td>Улыбка радуги</td><td>300</td><td>12 000</td><td>49 200</td></tr>
            <tr><td>Булочные Вольчека</td><td>300</td><td>12 000</td><td>49 200</td></tr>
            <tr><td>Ростелеком</td><td>280</td><td>11 200</td><td>100 000</td></tr>
            <tr><td>Burger King</td><td>280</td><td>11 200</td><td>98 333</td></tr>
            <tr><td>Токио-сити</td><td>260</td><td>10 400</td><td>56 666</td></tr>
            <tr><td>Додо пицца</td><td>250</td><td>10 000</td><td>41 000</td></tr>
            <tr><td>ЛюдиЛюбят</td><td>250</td><td>10 000</td><td>50 400</td></tr>
            <tr><td>Вкусно и точка</td><td>250</td><td>10 000</td><td>49 200</td></tr>
            <tr><td>Теремок</td><td>240</td><td>9 600</td><td>83 640</td></tr>
          </tbody>
        </table>
      </div>
      </>
      )}
    </div>
  )
}

export default App
