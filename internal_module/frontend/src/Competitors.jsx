import './App.css'

// Company salary data
const COMPANY_SALARY_HEADERS = [
  'Название компании',
  'ЧТС',
  'Минимальная зарплата',
  'Максимальная зарплата'
];

const COMPANY_SALARY_DATA = [
  ['Яндекс Лавка', '400', '16000', '93808'],
  ['Яндекс Еда', '400', '16000', '101516'],
  ['Самокат', '350', '14000', '63140'],
  ['Яндекс Крауд', '350', '14000', '75440'],
  ['Т-Банк', '330', '13200', '65600'],
  ['Ozon', '320', '12800', '106600'],
  ['Улыбка радуги', '300', '12000', '49200'],
  ['Булочные Вольчека', '300', '12000', '49200'],
  ['Ростелеком', '280', '11200', '100000'],
  ['Burger King', '280', '11200', '98333'],
  ['Токио-сити', '260', '10400', '56666'],
  ['Додо пицца', '250', '10000', '41000'],
  ['ЛюдиЛюбят', '250', '10000', '50400'],
  ['Вкусно и точка', '250', '10000', '49200'],
  ['Теремок', '240', '9600', '83640']
];

function Competitors() {
  return (
    <div className="container">
      <div className="header">
        <h1>Конкуренты</h1>
        <p className="competitors-subtitle">Сравнение зарплат по компаниям</p>
      </div>

      <div className="company-salary-table-card">
        <h3>Зарплаты по компаниям</h3>
        <div className="table-container">
          <table className="company-salary-table">
            <thead>
              <tr>
                {COMPANY_SALARY_HEADERS.map((header, index) => (
                  <th key={index}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPANY_SALARY_DATA.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>
                      {cellIndex > 0 ? Number(cell).toLocaleString() : cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Competitors
