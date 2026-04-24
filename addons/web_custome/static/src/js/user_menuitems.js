/** @odoo-module alias=web.custome **/

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { preferencesItem, supportItem, documentationItem, odooAccountItem } from "@web/webclient/user_menu/user_menu_items";

export function UserLog(env) {
    return Object.assign(
        {},
        preferencesItem(env),
        {
            description: _t("My profile"),
        }
    );
}
function ItriSol(env) {
    const documentationURL = "https://itrisol.com";
    return {
        type: "item",
        id: "documentation",
                description: _t("ItriSol"),
        href: documentationURL,
        callback: () => {
            browser.open(documentationURL, "_blank");
        },
        sequence: 10,
    };
}

registry.category("user_menuitems").add('profile', UserLog, { force: true })
registry.category("user_menuitems").add('itrisol', ItriSol)
registry.category("user_menuitems").remove('odoo_account')
registry.category("user_menuitems").remove('support')
registry.category("user_menuitems").remove('documentation')
