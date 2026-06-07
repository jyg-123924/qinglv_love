(function () {
  const display = document.getElementById('calc-display');
  const processEl = document.getElementById('calc-process');
  if (!display) return;

  let current = '0';
  let previous = '';
  let operator = '';
  let resetNext = false;

  const OP_SYMBOL = { '+': '+', '-': '−', '*': '×', '/': '÷' };

  function updateDisplay() {
    display.value = current.length > 12 ? parseFloat(current).toExponential(6) : current;
  }

  function updateProcess(text) {
    if (processEl) processEl.textContent = text;
  }

  function formatNum(val) {
    if (val === '错误') return val;
    const n = parseFloat(val);
    if (isNaN(n)) return val;
    return String(parseFloat(n.toPrecision(12)));
  }

  function buildProcess(showSecond) {
    if (!operator || !previous) {
      updateProcess('');
      return;
    }
    const sym = OP_SYMBOL[operator] || operator;
    if (showSecond) {
      updateProcess(`${formatNum(previous)} ${sym} ${formatNum(current)} =`);
    } else {
      updateProcess(`${formatNum(previous)} ${sym}`);
    }
  }

  function inputNum(val) {
    if (resetNext) {
      current = val;
      resetNext = false;
    } else {
      current = current === '0' ? val : current + val;
    }
    if (operator && previous) buildProcess(true);
    else updateProcess('');
    updateDisplay();
  }

  function inputDot() {
    if (resetNext) {
      current = '0.';
      resetNext = false;
    } else if (!current.includes('.')) {
      current += '.';
    }
    if (operator && previous) buildProcess(true);
    updateDisplay();
  }

  function clear() {
    current = '0';
    previous = '';
    operator = '';
    resetNext = false;
    updateProcess('');
    updateDisplay();
  }

  function backspace() {
    current = current.length > 1 ? current.slice(0, -1) : '0';
    if (operator && previous) buildProcess(true);
    updateDisplay();
  }

  function setOp(op) {
    if (operator && !resetNext) calculate(false);
    previous = current;
    operator = op;
    resetNext = true;
    buildProcess(false);
    updateDisplay();
  }

  let calcLogged = false;

  function logCalculatorUse() {
    if (calcLogged) return;
    calcLogged = true;
    const who = localStorage.getItem('qinglv_who') || '1';
    const body = new URLSearchParams({ action: 'calculator', who });
    fetch('/activity', { method: 'POST', body });
  }

  function calculate(showFull) {
    if (!operator || !previous) return;
    const a = parseFloat(previous);
    const b = parseFloat(current);
    let result;
    switch (operator) {
      case '+': result = a + b; break;
      case '-': result = a - b; break;
      case '*': result = a * b; break;
      case '/': result = b === 0 ? NaN : a / b; break;
      default: return;
    }
    if (showFull !== false) {
      buildProcess(true);
      logCalculatorUse();
    }
    current = isNaN(result) ? '错误' : String(parseFloat(result.toPrecision(12)));
    operator = '';
    previous = '';
    resetNext = true;
    updateDisplay();
  }

  function percent() {
    current = String(parseFloat(current) / 100);
    if (operator && previous) buildProcess(true);
    updateDisplay();
  }

  document.querySelectorAll('.calc-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      const value = btn.dataset.value;
      switch (action) {
        case 'num': inputNum(value); break;
        case 'dot': inputDot(); break;
        case 'op': setOp(value); break;
        case 'equals': calculate(true); break;
        case 'clear': clear(); break;
        case 'back': backspace(); break;
        case 'percent': percent(); break;
      }
    });
  });
})();
