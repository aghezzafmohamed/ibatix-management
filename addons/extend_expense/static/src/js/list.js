/** @odoo-module */

import { ExpenseListController, ExpenseListRenderer } from '@hr_expense/mixins/document_upload';

import { registry } from '@web/core/registry';
import { listView } from "@web/views/list/list_view";

registry.category('views').add('itrisol_hr_expense_tree', {
    ...listView,
    buttonTemplate: 'extend_expense.ListButtons',
    Controller: ExpenseListController,
    Renderer: ExpenseListRenderer,
});
