/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { patch } from "@web/core/utils/patch";

patch(KanbanRecord.prototype, {
    async update(recordData) {
        console.log("🔄 KanbanRecord update triggered:", recordData);  // ✅ LOG ADDED

        await this._super(recordData);

        // Check if state was changed
        if ("state" in recordData && recordData.state !== this.props.record.state.raw_value) {
            console.log("📦 State changed — reloading Kanban view...");
            this.props.record.model.root.load();
        }
    }
});
