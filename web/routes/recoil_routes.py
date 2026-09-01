"""Recoil / global settings API for rebuild web UI."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template_string, request

from app.core.config import load_config, save_config
from app.recoil.engine import invalidate_config_cache, reset_recoil_state
from app.recoil.weapon_data import WeaponData
from web.input_status import get_input_status

recoil_bp = Blueprint('recoil', __name__, url_prefix='/api/recoil')

_hotkey_binding_active = False


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes'}


def _update_config(keys: list[str], value) -> None:
    config = load_config()
    for key in keys:
        config[key] = value
    save_config(config)
    invalidate_config_cache()


def _normalize_input_method(raw: str) -> str:
    value = (raw or '').strip().lower()
    if value in {'hardware', 'makcu'}:
        return 'makcu'
    if value in {'software', 'win32'}:
        return 'win32'
    return value or 'makcu'


@recoil_bp.route('/toggle', methods=['POST'])
def toggle():
    _update_config(['recoil_enabled'], _parse_bool(request.form.get('recoil_enabled', False)))
    return '', 204


@recoil_bp.route('/require_rmb', methods=['POST'])
def require_rmb():
    _update_config(['recoil_require_rmb'], _parse_bool(request.form.get('recoil_require_rmb', False)))
    return '', 204


@recoil_bp.route('/input_method', methods=['POST'])
def input_method():
    method = _normalize_input_method(request.form.get('recoil_input_method', 'makcu'))
    config = load_config()
    config['mouse_input_method'] = method
    save_config(config)
    invalidate_config_cache()
    label = 'Makcu' if method == 'makcu' else 'Win32 (dev)'
    warning = '' if method == 'makcu' else (
        '<div class="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 '
        'text-amber-200/80 text-xs"><p><strong class="text-amber-400">Dual-PC warning</strong> '
        f'{label} moves the mouse on <em>this</em> PC only. Use <strong>Hardware (Makcu)</strong> for gaming PC.</p></div>'
    )
    return render_template_string('{{ html|safe }}', html=warning)


@recoil_bp.route('/cloud_username', methods=['POST'])
def cloud_username():
    name = (request.form.get('cloud_username') or 'Anonymous').strip() or 'Anonymous'
    _update_config(['cloud_username'], name)
    return '', 204


@recoil_bp.route('/hotkey-binding', methods=['POST'])
def hotkey_binding():
    global _hotkey_binding_active
    _hotkey_binding_active = _parse_bool(request.form.get('active', False))
    return '', 204


@recoil_bp.route('/hotkey', methods=['POST'])
def set_hotkey():
    field = (request.form.get('field') or 'global_toggle_hotkey').strip()
    value = (request.form.get('value') or 'M5').strip() or 'M5'
    if field not in {'global_toggle_hotkey'}:
        return jsonify({'success': False, 'message': f'Unknown field: {field}'}), 400
    config = load_config()
    config['global_toggle_hotkey'] = value
    config['recoil_keybind'] = value
    save_config(config)
    invalidate_config_cache()
    return jsonify({'success': True, 'field': field, 'value': value})


@recoil_bp.route('/state', methods=['GET'])
def recoil_state():
    config = load_config()
    return jsonify({
        'ok': True,
        'recoil_enabled': bool(config.get('recoil_enabled')),
        'recoil_keybind': 'ALWAYS',
        'global_toggle_hotkey': config.get('global_toggle_hotkey', 'M5'),
    })


@recoil_bp.route('/cs2_weapon', methods=['POST'])
def cs2_weapon():
    weapon = (request.form.get('weapon') or request.form.get('cs2_weapon') or 'assault_rifle').strip()
    config = load_config()
    config.setdefault('recoil_cs2_settings', {})['cs2_weapon'] = weapon
    save_config(config)
    invalidate_config_cache()
    reset_recoil_state()
    return '', 204


@recoil_bp.route('/cs2_sensitivity', methods=['POST'])
def cs2_sensitivity():
    try:
        sensitivity = float(request.form.get('sensitivity', 1.25))
    except (TypeError, ValueError):
        sensitivity = 1.25
    config = load_config()
    config.setdefault('recoil_cs2_settings', {})['cs2_sensitivity'] = sensitivity
    save_config(config)
    invalidate_config_cache()
    return '', 204


@recoil_bp.route('/randomisation', methods=['POST'])
def randomisation():
    _update_config(['recoil_randomisation'], _parse_bool(request.form.get('recoil_randomisation', False)))
    return '', 204


@recoil_bp.route('/random_strength', methods=['POST'])
def random_strength():
    try:
        value = float(request.form.get('recoil_random_strength', 5.0))
    except (TypeError, ValueError):
        value = 5.0
    _update_config(['recoil_random_strength'], value)
    return '', 204


@recoil_bp.route('/x_control', methods=['POST'])
def x_control():
    try:
        value = int(float(request.form.get('recoil_x_control', 100)))
    except (TypeError, ValueError):
        value = 100
    _update_config(['recoil_x_control'], value)
    return '', 204


@recoil_bp.route('/y_control', methods=['POST'])
def y_control():
    try:
        value = int(float(request.form.get('recoil_y_control', 100)))
    except (TypeError, ValueError):
        value = 100
    _update_config(['recoil_y_control'], value)
    return '', 204


@recoil_bp.route('/makcu_status', methods=['GET'])
def makcu_status():
    status = get_input_status()
    return jsonify({
        'ok': True,
        'makcu_connected': status['makcu_hardware'],
        'makcu_dev_fallback': status['makcu_dev_fallback'],
        'makcu_port': status.get('makcu_port', '—'),
        'input_status': status['input_status'],
    })


@recoil_bp.route('/hardware-check', methods=['GET'])
def hardware_check():
    status = get_input_status()
    return render_template_string(
        """
        <div id="hardware-status" hx-get="/api/recoil/hardware-check" hx-trigger="every 10s"
             hx-swap="outerHTML" class="flex flex-wrap items-center gap-2">
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border {{ input_style }}">
                <div class="w-2 h-2 rounded-full {{ input_dot }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">{{ input_label }}: {{ input_status }}</span>
            </div>
            <div class="flex items-center gap-2 px-3 py-1 rounded-full border {{ integrity_color }}">
                <div class="w-2 h-2 rounded-full {{ dot_color }}"></div>
                <span class="text-[10px] font-bold uppercase tracking-widest">Integrity: {{ integrity_level }}</span>
            </div>
        </div>
        """,
        **status,
    )


@recoil_bp.route('/cs2_weapon_options', methods=['GET'])
def cs2_weapon_options():
    category = (request.args.get('category') or 'rifle').strip().lower()
    if category not in WeaponData.CATEGORY_LABELS:
        category = 'rifle'
    config = load_config()
    active = config.get('recoil_cs2_settings', {}).get('cs2_weapon', 'assault_rifle')
    labels = WeaponData.weapon_labels()
    options = []
    for weapon_id in WeaponData.weapons_in_category(category):
        selected = 'selected' if weapon_id == active else ''
        label = labels.get(weapon_id, weapon_id)
        options.append(f'<option value="{weapon_id}" {selected}>{label}</option>')
    return '\n'.join(options), 200, {'Content-Type': 'text/html; charset=utf-8'}
