// These tables map the js keyboard keys to the spice equivalent
wdi.KeymapIT = function() {

    // regular keys with associated chars. The columns  means all the event flux to activate the key (i.e. [key up, key down])
    // all the js events associated to these keys should have a charKey associated
    var charmapIT = {};
    charmapIT['\\']   = [[0x29, 0, 0, 0], [0xA9, 0, 0, 0]];
    charmapIT['|']   = [[0x2A, 0, 0, 0], [0x29, 0, 0, 0], [0xA9, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['1']   = [[0x2, 0, 0, 0], [0x82, 0, 0, 0]];
    charmapIT['!']   = [[0x2A, 0, 0, 0], [0x2, 0, 0, 0], [0x82, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['2']   = [[0x3, 0, 0, 0], [0x83, 0, 0, 0]];
    charmapIT['"']   = [[0x2A, 0, 0, 0], [0x3, 0, 0, 0], [0x83, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['3']   = [[0x4, 0, 0, 0], [0x84, 0, 0, 0]];
    charmapIT['£']   = [[0x2A, 0, 0, 0], [0x4, 0, 0, 0], [0x84, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['4']   = [[0x5, 0, 0, 0], [0x85, 0, 0, 0]];
    charmapIT['$']   = [[0x2A, 0, 0, 0], [0x5, 0, 0, 0], [0x85, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['5']   = [[0x6, 0, 0, 0], [0x86, 0, 0, 0]];
    charmapIT['%']   = [[0x2A, 0, 0, 0], [0x6, 0, 0, 0], [0x86, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['6']   = [[0x7, 0, 0, 0], [0x87, 0, 0, 0]];
    charmapIT['&']   = [[0x2A, 0, 0, 0], [0x7, 0, 0, 0], [0x87, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['7']   = [[0x8, 0, 0, 0], [0x88, 0, 0, 0]];
    charmapIT['/']   = [[0x2A, 0, 0, 0], [0x8, 0, 0, 0], [0x88, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['8']   = [[0x9, 0, 0, 0], [0x89, 0, 0, 0]];
    charmapIT['(']   = [[0x2A, 0, 0, 0], [0x9, 0, 0, 0], [0x89, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['9']   = [[0x0A, 0, 0, 0], [0x8A, 0, 0, 0]];
    charmapIT[')']   = [[0x2A, 0, 0, 0], [0x0A, 0, 0, 0], [0x8A, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['0']   = [[0x0B, 0, 0, 0], [0x8B, 0, 0, 0]];
    charmapIT['=']   = [[0x2A, 0, 0, 0], [0x0B, 0, 0, 0], [0x8B, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['\'']  = [[0x0C, 0, 0, 0], [0x8C, 0, 0, 0]];
    charmapIT['?']   = [[0x2A, 0, 0, 0], [0x0C, 0, 0, 0], [0x8C, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['`']   = [[0xE0, 0x38, 0, 0], [0x0C, 0, 0, 0], [0x8C, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['ì']   = [[0x0D, 0, 0, 0], [0x8D, 0, 0, 0]];
    charmapIT['^']   = [[0x2A, 0, 0, 0], [0x0D, 0, 0, 0], [0x8D, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['~']   = [[0xE0, 0x38, 0, 0], [0x0D, 0, 0, 0], [0x8D, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['q']   = [[0x10, 0, 0, 0], [0x90, 0, 0, 0]];
    charmapIT['Q']   = [[0x2A, 0, 0, 0], [0x10, 0, 0, 0], [0x90, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['w']   = [[0x11, 0, 0, 0], [0x91, 0, 0, 0]];
    charmapIT['W']   = [[0x2A, 0, 0, 0], [0x11, 0, 0, 0], [0x91, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['e']   = [[0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapIT['E']   = [[0x2A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['€']   = [[0xE0, 0x38, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['r']   = [[0x13, 0, 0, 0], [0x93, 0, 0, 0]];
    charmapIT['R']   = [[0x2A, 0, 0, 0], [0x13, 0, 0, 0], [0x93, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['t']   = [[0x14, 0, 0, 0], [0x94, 0, 0, 0]];
    charmapIT['T']   = [[0x2A, 0, 0, 0], [0x14, 0, 0, 0], [0x94, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['y']   = [[0x15, 0, 0, 0], [0x95, 0, 0, 0]];
    charmapIT['Y']   = [[0x2A, 0, 0, 0], [0x15, 0, 0, 0], [0x95, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['u']   = [[0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapIT['U']   = [[0x2A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['i']   = [[0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapIT['I']   = [[0x2A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['o']   = [[0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapIT['O']   = [[0x2A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['p']   = [[0x19, 0, 0, 0], [0x99, 0, 0, 0]];
    charmapIT['P']   = [[0x2A, 0, 0, 0], [0x19, 0, 0, 0], [0x99, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['è']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0]];
    charmapIT['é']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['[']   = [[0xE0, 0x38, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['{']   = [[0xE0, 0x38, 0, 0], [0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['+']   = [[0x1B, 0, 0, 0], [0x9B, 0, 0, 0]];
    charmapIT['*']   = [[0x2A, 0, 0, 0], [0x1B, 0, 0, 0], [0x9B, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT[']']   = [[0xE0, 0x38, 0, 0], [0x1B, 0, 0, 0], [0x9B, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['}']   = [[0xE0, 0x38, 0, 0], [0x2A, 0, 0, 0], [0x1B, 0, 0, 0], [0x9B, 0, 0, 0], [0xAA, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['a']   = [[0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapIT['A']   = [[0x2A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['s']   = [[0x1F, 0, 0, 0], [0x9F, 0, 0, 0]];
    charmapIT['S']   = [[0x2A, 0, 0, 0], [0x1F, 0, 0, 0], [0x9F, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['d']   = [[0x20, 0, 0, 0], [0xA0, 0, 0, 0]];
    charmapIT['D']   = [[0x2A, 0, 0, 0], [0x20, 0, 0, 0], [0xA0, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['f']   = [[0x21, 0, 0, 0], [0xA1, 0, 0, 0]];
    charmapIT['F']   = [[0x2A, 0, 0, 0], [0x21, 0, 0, 0], [0xA1, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['g']   = [[0x22, 0, 0, 0], [0xA2, 0, 0, 0]];
    charmapIT['G']   = [[0x2A, 0, 0, 0], [0x22, 0, 0, 0], [0xA2, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['h']   = [[0x23, 0, 0, 0], [0xA3, 0, 0, 0]];
    charmapIT['H']   = [[0x2A, 0, 0, 0], [0x23, 0, 0, 0], [0xA3, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['j']   = [[0x24, 0, 0, 0], [0xA4, 0, 0, 0]];
    charmapIT['J']   = [[0x2A, 0, 0, 0], [0x24, 0, 0, 0], [0xA4, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['k']   = [[0x25, 0, 0, 0], [0xA5, 0, 0, 0]];
    charmapIT['K']   = [[0x2A, 0, 0, 0], [0x25, 0, 0, 0], [0xA5, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['l']   = [[0x26, 0, 0, 0], [0xA6, 0, 0, 0]];
    charmapIT['L']   = [[0x2A, 0, 0, 0], [0x26, 0, 0, 0], [0xA6, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['ò']   = [[0x27, 0, 0, 0], [0xA7, 0, 0, 0]];
    charmapIT['ç']   = [[0x2A, 0, 0, 0], [0x27, 0, 0, 0], [0xA7, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['@']   = [[0xE0, 0x38, 0, 0], [0x27, 0, 0, 0], [0xA7, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['à']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0]];
    charmapIT['°']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['#']   = [[0xE0, 0x38, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapIT['ù']   = [[0x2B, 0, 0, 0], [0xAB, 0, 0, 0]];
    charmapIT['§']   = [[0x2A, 0, 0, 0], [0x2B, 0, 0, 0], [0xAB, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['<']   = [[0x56, 0, 0, 0], [0xD6, 0, 0, 0]];
    charmapIT['>']   = [[0x2A, 0, 0, 0], [0x56, 0, 0, 0], [0xD6, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['z']   = [[0x2C, 0, 0, 0], [0xAC, 0, 0, 0]];
    charmapIT['Z']   = [[0x2A, 0, 0, 0], [0x2C, 0, 0, 0], [0xAC, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['x']   = [[0x2D, 0, 0, 0], [0xAD, 0, 0, 0]];
    charmapIT['X']   = [[0x2A, 0, 0, 0], [0x2D, 0, 0, 0], [0xAD, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['c']   = [[0x2E, 0, 0, 0], [0xAE, 0, 0, 0]];
    charmapIT['C']   = [[0x2A, 0, 0, 0], [0x2E, 0, 0, 0], [0xAE, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['v']   = [[0x2F, 0, 0, 0], [0xAF, 0, 0, 0]];
    charmapIT['V']   = [[0x2A, 0, 0, 0], [0x2F, 0, 0, 0], [0xAF, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['b']   = [[0x30, 0, 0, 0], [0xB0, 0, 0, 0]];
    charmapIT['B']   = [[0x2A, 0, 0, 0], [0x30, 0, 0, 0], [0xB0, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['n']   = [[0x31, 0, 0, 0], [0xB1, 0, 0, 0]];
    charmapIT['N']   = [[0x2A, 0, 0, 0], [0x31, 0, 0, 0], [0xB1, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['m']   = [[0x32, 0, 0, 0], [0xB2, 0, 0, 0]];
    charmapIT['M']   = [[0x2A, 0, 0, 0], [0x32, 0, 0, 0], [0xB2, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT[',']   = [[0x33, 0, 0, 0], [0xB3, 0, 0, 0]];
    charmapIT[';']   = [[0x2A, 0, 0, 0], [0x33, 0, 0, 0], [0xB3, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['.']   = [[0x34, 0, 0, 0], [0xB4, 0, 0, 0]];
    charmapIT[':']   = [[0x2A, 0, 0, 0], [0x34, 0, 0, 0], [0xB4, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT['-']   = [[0x35, 0, 0, 0], [0xB5, 0, 0, 0]];
    charmapIT['_']   = [[0x2A, 0, 0, 0], [0x35, 0, 0, 0], [0xB5, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapIT[' ']   = [[0x39, 0, 0, 0], [0xb9, 0, 0, 0]];

    // keyboard keys without character associated.
    // all the js events associated to these keys should have a keyChar associated
    var keymapIT = [];

    keymapIT[27]                 = 0x1; // ESC
    keymapIT[9]                 = 0x0F; // TAB
    //keymapIT[20]                = 0x3A; // CAPS LOCK => see the charmap, all the capital letters and shift chars send a shift in their sequence
    keymapIT[16]                = 0x2A; // LEFT SHIFT and RIGHT SHIFT
    keymapIT[91]                = 0x1D; // LEFT GUI (META, COMMAND) BINDED TO CONTROL (why? 0x5B)
    keymapIT[17]                = 0x1D; // LEFT CONTROL and RIGHT CONTROL
    //keymapIT[32]                = 0x39; // SPACE => see the charmap
    keymapIT[8]                 = 0x0E; // BACKSPACE
    keymapIT[12]                = 0x4C; // KP_BEGIN (showkey -s: 0x4C, 0xCC)
    keymapIT[13]                = 0x1C; // ENTER
    //keymapIT[225]               = 0x38; // RIGHT ALT (ALT GR) => see the charmap, all the altgr chars send a altgr in their sequence
    keymapIT[18]                = 0x38; // LEFT ALT
    //keymapIT[19]                = 0x??; // PAUSE (showkey -s: 0xE1 0x1D 0x45, 0xE1 0x9D 0xC5)
    //keymapIT[92]                = 0x5C; // RIGHT GUI (WINDOWS) (I get 91 for the right too)
    keymapIT[93]                = 0x5D; // MENU
    keymapIT[38]                = 0x48; // UP ARROW
    keymapIT[37]                = 0x4B; // LEFT ARROW
    keymapIT[40]                = 0x50; // DOWN ARROW
    keymapIT[39]                = 0x4D; // RIGHT ARROW
    //keymapIT[42]                = 0x??; // PRINT (showkey -s: 0xE0 0x2A 0xE0 0x37, 0xE0 0xAA 0xE0 0xB7)
    keymapIT[45]                = 0x52; // INSERT
    keymapIT[46]                = 0x53; // DELETE
    keymapIT[36]                = 0x47; // HOME
    keymapIT[35]                = 0x4F; // END
    keymapIT[33]                = 0x49; // PAGE UP
    keymapIT[34]                = 0x51; // PAGE DOWN
    keymapIT[144]               = 0x45; // NUM LOCK
    keymapIT[145]                = 0x46; // SCROLL LOCK
    keymapIT[112]                = 0x3B; // F1
    keymapIT[113]                = 0x3C; // F2
    keymapIT[114]                = 0x3D; // F3
    keymapIT[115]                = 0x3E; // F4
    keymapIT[116]                = 0x3F; // F5
    keymapIT[117]                = 0x40; // F6
    keymapIT[118]                = 0x41; // F7
    keymapIT[119]                = 0x42; // F8
    keymapIT[120]                = 0x43; // F9
    keymapIT[121]                = 0x44; // F10
    keymapIT[122]                = 0x57; // F11
    keymapIT[123]                = 0x58; // F12

    // combination keys with ctrl
    var ctrlKeymapIT = [];

    ctrlKeymapIT[65]                = 0x1E; // a
    ctrlKeymapIT[81]                = 0x10; // q
    ctrlKeymapIT[87]                = 0x11; // w
    ctrlKeymapIT[69]                = 0x12; // e
    ctrlKeymapIT[82]                = 0x13; // r
    ctrlKeymapIT[84]                = 0x14; // t
    ctrlKeymapIT[89]                = 0x15; // y
    ctrlKeymapIT[85]                = 0x16; // u
    ctrlKeymapIT[73]                = 0x17; // i
    ctrlKeymapIT[79]                = 0x18; // o
    ctrlKeymapIT[80]                = 0x19; // p
    ctrlKeymapIT[65]                = 0x1E; // a
    ctrlKeymapIT[83]                = 0x1F; // s
    ctrlKeymapIT[68]                = 0x20; // d
    ctrlKeymapIT[70]                = 0x21; // f
    ctrlKeymapIT[71]                = 0x22; // g
    ctrlKeymapIT[72]                = 0x23; // h
    ctrlKeymapIT[74]                = 0x24; // j
    ctrlKeymapIT[75]                = 0x25; // k
    ctrlKeymapIT[76]                = 0x26; // l
    ctrlKeymapIT[90]                = 0x2C; // z
    ctrlKeymapIT[88]                = 0x2D; // x
    ctrlKeymapIT[67]                = 0x2E; // c
    //ctrlKeymapIT[86]                = 0x2F; // v      to enable set disableClipboard = true in run.js
    ctrlKeymapIT[66]                = 0x30; // b
    ctrlKeymapIT[78]                = 0x31; // n
    ctrlKeymapIT[77]                = 0x32; // m

    // reserved ctrl+? combinations we want to intercept from browser and inject manually to spice
    var reservedCtrlKeymap = [];
    reservedCtrlKeymap[86] = 0x2F;

    return {
        getKeymap: function() {
            return keymapIT;
        },

        getCtrlKeymap: function() {
            return ctrlKeymapIT;
        },

        getReservedCtrlKeymap: function() {
            return reservedCtrlKeymap;
        },

        getCharmap: function() {
            return charmapIT;
        },

        setCtrlKey: function (key, val) {
            ctrlKeymapIT[key] = val;
        }
    };
}( );
