wdi.keyShortcutsHandled = {
    CTRLV: 0
}

wdi.Keymap = {
    keymap: {},
    ctrlKeymap: {},
    charmap: {},
    ctrlPressed: false,
    twoBytesScanCodes: [0x5B, 0xDB, /*0x38, 0xB8,*/ 0x5C, 0xDC, 0x1D, 0x9D, 0x5D, 0xDD, 0x52, 0xD2, 0x53, 0xD3, 0x4B, 0xCB, 0x47, 0xC9, 0x4F, 0xCF, 0x48, 0xC8, 0x50, 0xD0, 0x49, 0xC9, 0x51, 0xD1, 0x4D, 0xCD, 0x1C, 0x9C],

    loadKeyMap: function(layout) {
        try {
            this.keymap = wdi['Keymap' + layout.toUpperCase()].getKeymap();
            this.ctrlKeymap = wdi['Keymap' + layout.toUpperCase()].getCtrlKeymap();
            this.reservedCtrlKeymap =  wdi['Keymap' + layout.toUpperCase()].getReservedCtrlKeymap();
            this.charmap = wdi['Keymap' + layout.toUpperCase()].getCharmap();
        } catch(e) {
			this.keymap = wdi.KeymapES.getKeymap();
            this.ctrlKeymap = wdi.KeymapES.getCtrlKeymap();
            this.reservedCtrlKeymap =  wdi.KeymapES.getReservedCtrlKeymap();
            this.charmap = wdi.KeymapES.getCharmap();
		}
    },

    isInKeymap: function(keycode) {
        if (this.keymap[keycode] === undefined) return false;
        else return true;
    },

    /**
     * Returns the associated spice key code from the given browser keyboard event
     * @param e
     * @returns {*}
     */
    getScanCodes: function(e) {
		if (e['hasScanCode']) {
			return e['scanCode'];
		} else if (this.handledByCtrlKeyCode(e['type'], e['keyCode'], e['generated'])) {// before doing anything else we check if the event about to be handled has to be intercepted
            return this.getScanCodeFromKeyCode(e['keyCode'], e['type'], this.ctrlKeymap, this.reservedCtrlKeymap);
        } else if (this.handledByCharmap(e['type'])) {
            return this.getScanCodesFromCharCode(e['charCode']);
        } else if (this.handledByNormalKeyCode(e['type'], e['keyCode'])) {
            return this.getScanCodeFromKeyCode(e['keyCode'], e['type'], this.keymap);
        } else {
            return [];
        }
    },

    getScanCodeFromKeyCode: function(keyCode, type, keymap, additionalKeymap) {
        this.controlPressed(keyCode, type);
        var key = null;
        if(keyCode in keymap) {
            key = keymap[keyCode];
        } else {
            key = additionalKeymap[keyCode];
        }
        if (key === undefined) return [];
        if (key < 0x100) {
            if (type == 'keydown') {
                return [this.makeKeymap(key)];
            } else if (type == 'keyup') {
                return [this.makeKeymap(key | 0x80)];
            }
        } else {
            if (type == 'keydown') {
                return [this.makeKeymap(0xe0 | ((key - 0x100) << 8))];
            } else if (type == 'keyup') {
                return [this.makeKeymap(0x80e0 | ((key - 0x100) << 8))];
            }
        }
        return key;
    },

    controlPressed: function(keyCode, type) {
        if (keyCode === 17 || keyCode === 91) {  // Ctrl or CMD key
            if (type === 'keydown') this.ctrlPressed = true;
            else if (type === 'keyup') this.ctrlPressed = false;
        }
    },

    handledByCtrlKeyCode: function(type, keyCode, generated) {
        if (type === 'keydown' || type === 'keyup' || type === 'keypress') {
            if (this.ctrlPressed) {
                if (type === 'keypress') {
                    return true;
                }

                if (this.ctrlKeymap[keyCode]) {
                    return true;  // is the second key in a keyboard shortcut (i.e. the x in Ctrl+x)
                }

                //check if the event is a fake event generated from our gui or programatically
                if(generated && this.reservedCtrlKeymap[keyCode]) {
                    return true;
                }
            }
        }
        return false;
    },

    handledByNormalKeyCode: function(type, keyCode) {
        if (type === 'keydown' || type === 'keyup') {
            if (this.keymap[keyCode]) {
                return true;
            }
        }
        return false;
    },

    handledByCharmap: function(type) {
        if (type === 'inputmanager') return true;
        else return false;
    },

    getScanCodesFromCharCode: function(charCode) {
        var scanCode = this.charmap[String.fromCharCode(charCode)];
        if (scanCode === undefined) scanCode = [];
        return scanCode;
    },

    makeKeymap: function(scancode) {
        if ($.inArray(scancode, this.twoBytesScanCodes) != -1) {
            return [0xE0, scancode, 0, 0];
        } else {
            return [scancode, 0, 0];
        }
    }
}
