/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillUnmount, onWillUpdateProps, useRef, useState } from "@odoo/owl";

const DEFAULT_CENTER = [24.7136, 46.6753]; // Riyadh, as a sane default map center
const DEFAULT_ZOOM = 14;

/**
 * Interactive OpenStreetMap / Leaflet widget used to draw a field boundary
 * polygon. The boundary is stored as a JSON list of [lng, lat] pairs in the
 * underlying Text field. Also writes back the polygon centroid into the
 * fields configured through the `lat_field` / `lng_field` widget options,
 * when present on the record.
 */
class AgriFieldMapWidget extends Component {
    static template = "leapai_agriculture.FieldMapWidget";
    static props = { ...standardFieldProps };

    setup() {
        this.mapRef = useRef("map");
        this.notification = useService("notification");
        this.state = useState({ hasBoundary: !!this.props.record.data[this.props.name] });
        this.map = null;
        this.polygon = null;
        this.drawnPoints = [];
        this.drawing = false;

        onMounted(() => this._mountMap());
        onWillUpdateProps((nextProps) => {
            const nextValue = nextProps.record.data[this.props.name];
            if (this.map && nextValue !== this.props.record.data[this.props.name]) {
                this._loadBoundary(nextValue);
            }
        });
        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }

    get readonly() {
        return this.props.readonly;
    }

    _mountMap() {
        if (!this.mapRef.el || typeof L === "undefined") {
            return;
        }
        const options = this.props.options || {};
        const latField = options.lat_field;
        const lngField = options.lng_field;
        const data = this.props.record.data;
        const lat = (latField && data[latField]) || DEFAULT_CENTER[0];
        const lng = (lngField && data[lngField]) || DEFAULT_CENTER[1];

        this.map = L.map(this.mapRef.el, {
            center: [lat || DEFAULT_CENTER[0], lng || DEFAULT_CENTER[1]],
            zoom: DEFAULT_ZOOM,
        });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19,
        }).addTo(this.map);

        this._loadBoundary(this.props.record.data[this.props.name]);

        if (!this.readonly) {
            this.map.on("click", (ev) => this._onMapClick(ev));
        }
    }

    _loadBoundary(value) {
        this._clearPolygon();
        this.drawnPoints = [];
        if (!value) {
            this.state.hasBoundary = false;
            return;
        }
        let coords;
        try {
            coords = JSON.parse(value);
        } catch {
            return;
        }
        if (!Array.isArray(coords) || !coords.length) {
            this.state.hasBoundary = false;
            return;
        }
        this.state.hasBoundary = true;
        // stored as [lng, lat] pairs -> Leaflet wants [lat, lng]
        const latLngs = coords.map(([lng, lat]) => [lat, lng]);
        this.polygon = L.polygon(latLngs, { color: "#2e7d32" }).addTo(this.map);
        this.drawnPoints = coords;
        try {
            this.map.fitBounds(this.polygon.getBounds(), { padding: [20, 20] });
        } catch {
            // ignore bounds errors on degenerate polygons
        }
    }

    _clearPolygon() {
        if (this.polygon) {
            this.map.removeLayer(this.polygon);
            this.polygon = null;
        }
    }

    _onMapClick(ev) {
        if (this.readonly) {
            return;
        }
        this.drawnPoints.push([ev.latlng.lng, ev.latlng.lat]);
        this._clearPolygon();
        const latLngs = this.drawnPoints.map(([lng, lat]) => [lat, lng]);
        if (this.drawnPoints.length === 1) {
            this.polygon = L.circleMarker(latLngs[0], { radius: 4, color: "#2e7d32" }).addTo(this.map);
        } else {
            this.polygon = L.polygon(latLngs, { color: "#2e7d32" }).addTo(this.map);
        }
        this.state.hasBoundary = this.drawnPoints.length >= 3;
    }

    async onFinishBoundary() {
        if (this.drawnPoints.length < 3) {
            this.notification.add("Click at least 3 points on the map to draw a boundary.", {
                type: "warning",
            });
            return;
        }
        const closed = [...this.drawnPoints, this.drawnPoints[0]];
        const value = JSON.stringify(closed);
        await this.props.record.update({ [this.props.name]: value });

        const options = this.props.options || {};
        const latField = options.lat_field;
        const lngField = options.lng_field;
        if (latField || lngField) {
            const lat = closed.reduce((s, p) => s + p[1], 0) / closed.length;
            const lng = closed.reduce((s, p) => s + p[0], 0) / closed.length;
            const vals = {};
            if (latField) {
                vals[latField] = lat;
            }
            if (lngField) {
                vals[lngField] = lng;
            }
            await this.props.record.update(vals);
        }
    }

    async onClearBoundary() {
        this.drawnPoints = [];
        this._clearPolygon();
        this.state.hasBoundary = false;
        await this.props.record.update({ [this.props.name]: false });
    }
}

registry.category("fields").add("agri_field_map", {
    component: AgriFieldMapWidget,
    supportedTypes: ["text"],
});
