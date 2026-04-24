/** @odoo-module **/
import { Component } from '@odoo/owl';
import { useRef, useState } from "@odoo/owl";
import { registry } from '@web/core/registry';

export class ProCalculator extends Component {
    setup() {
        super.setup();
        this.rootRef = useRef('root');
        this.displayRef = useRef('calcDisplay');
        this.historyRef = useRef('calcHistory');
        this.dragHandleRef = useRef('dragHandle');

        this.state = useState({
            x: 0,
            y: 0,
            isVisible: false,
        });

        this.currentInput = '';
        this.currentOperator = '';
        this.result = 0;
        this.history = '';

        this.dragStartX = 0;
        this.dragStartY = 0;
        this.isDragging = false;
    }

    toggleCalculator() {
        this.state.isVisible = !this.state.isVisible;
    }

    startDrag(ev) {
        ev.preventDefault();
        this.isDragging = true;
        this.dragStartX = ev.clientX - this.state.x;
        this.dragStartY = ev.clientY - this.state.y;

        const calcEl = this.rootRef.el.querySelector('.calculator-app');
        calcEl.classList.add('dragging');

        document.addEventListener('pointermove', this.onDragging);
        document.addEventListener('pointerup', this.stopDrag);
    }

    onDragging = (ev) => {
        if (!this.isDragging) return;
        this.state.x = ev.clientX - this.dragStartX;
        this.state.y = ev.clientY - this.dragStartY;
        this.updatePosition();
    }

    stopDrag = () => {
        this.isDragging = false;
        const calcEl = this.rootRef.el.querySelector('.calculator-app');
        calcEl.classList.remove('dragging');

        document.removeEventListener('pointermove', this.onDragging);
        document.removeEventListener('pointerup', this.stopDrag);
    }

    updatePosition() {
        const calcEl = this.rootRef.el.querySelector('.calculator-app');
        calcEl.style.transform = `translate(${this.state.x}px, ${this.state.y}px)`;
    }

    closeCalculator() {
        this.state.isVisible = false;
    }

    handleNumberClick(ev) {
        const number = ev.currentTarget.dataset.key;
        this.currentInput += number;
        this.displayRef.el.value = this.currentInput;
    }

    handleOperatorClick(ev) {
        const operator = ev.currentTarget.dataset.key;

        if (this.currentInput !== '') {
            if (this.currentOperator) {
                this.history += ` ${this.currentOperator} ${parseFloat(this.currentInput)}`;
                this.result = this.computeResult(this.result, parseFloat(this.currentInput), this.currentOperator);

                this.displayRef.el.value = this.result;
                this.historyRef.el.textContent = this.history;
                this.historyRef.el.scrollLeft = this.historyRef.el.scrollWidth;
            } else {
                this.result = parseFloat(this.currentInput);
                this.history = this.result.toString();
                this.historyRef.el.textContent = this.history;
            }
            this.currentInput = '';
            this.currentOperator = operator;
        }
    }

    handleEqualsClick() {
        if (this.currentInput !== '' && this.currentOperator) {
            this.result = this.computeResult(this.result, parseFloat(this.currentInput), this.currentOperator);
            this.displayRef.el.value = this.result;
            this.currentInput = this.result.toString();
            this.currentOperator = '';
        }
    }

    handleClearClick() {
        this.result = 0;
        this.currentInput = '';
        this.currentOperator = '';
        this.displayRef.el.value = '';
        this.history = '';
        this.historyRef.el.textContent = '';
    }

    handleDeleteClick() {
        this.currentInput = this.displayRef.el.value.slice(0, -1);
        this.displayRef.el.value = this.currentInput;
    }

    handleToggleSign() {
        if (!this.currentInput) return;
        this.currentInput = this.currentInput.startsWith('-') ? this.currentInput.slice(1) : '-' + this.currentInput;
        this.displayRef.el.value = this.currentInput;
    }

    handleDecimalClick() {
        if (!this.currentInput.includes('.')) {
            this.currentInput += '.';
            this.displayRef.el.value = this.currentInput;
        }
    }

    computeResult(num1, num2, operator) {
        switch (operator) {
            case '+': return num1 + num2;
            case '-': return num1 - num2;
            case '*': return num1 * num2;
            case '/': return num2 === 0 ? "Error" : num1 / num2;
            case '%': return (num1 / 100) * num2;
            default: return num2;
        }
    }
}

ProCalculator.template = 'ProCalculatorTool';

export const proCalculator = { Component: ProCalculator };
registry.category('systray').add('ProCalculator', proCalculator);
