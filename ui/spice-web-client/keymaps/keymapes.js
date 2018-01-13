// These tables map the js keyboard keys to the spice equivalent
wdi.KeymapES = function() {

    // regular keys with associated chars. The columns  means all the event flux to activate the key (i.e. [key up, key down])
    // all the js events associated to these keys should have a charKey associated
    var charmapES = {};
    charmapES['º']   = [[0x29, 0, 0, 0], [0xA9, 0, 0, 0]];
    charmapES['ª']   = [[0x2A, 0, 0, 0], [0x29, 0, 0, 0], [0xA9, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['\\']  = [[0xE0, 0x38, 0, 0], [0x29, 0, 0, 0], [0xA9, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['1']   = [[0x2, 0, 0, 0], [0x82, 0, 0, 0]];
    charmapES['!']   = [[0x2A, 0, 0, 0], [0x2, 0, 0, 0], [0x82, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['|']   = [[0xE0, 0x38, 0, 0], [0x2, 0, 0, 0], [0x82, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['2']   = [[0x3, 0, 0, 0], [0x83, 0, 0, 0]];
    charmapES['"']   = [[0x2A, 0, 0, 0], [0x3, 0, 0, 0], [0x83, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['@']   = [[0xE0, 0x38, 0, 0], [0x3, 0, 0, 0], [0x83, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['3']   = [[0x4, 0, 0, 0], [0x84, 0, 0, 0]];
    charmapES['·']   = [[0x2A, 0, 0, 0], [0x4, 0, 0, 0], [0x84, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['#']   = [[0xE0, 0x38, 0, 0], [0x4, 0, 0, 0], [0x84, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['4']   = [[0x5, 0, 0, 0], [0x85, 0, 0, 0]];
    charmapES['$']   = [[0x2A, 0, 0, 0], [0x5, 0, 0, 0], [0x85, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['~']   = [[0xE0, 0x38, 0, 0], [0x5, 0, 0, 0], [0x85, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['5']   = [[0x6, 0, 0, 0], [0x86, 0, 0, 0]];
    charmapES['%']   = [[0x2A, 0, 0, 0], [0x6, 0, 0, 0], [0x86, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['6']   = [[0x7, 0, 0, 0], [0x87, 0, 0, 0]];
    charmapES['&']   = [[0x2A, 0, 0, 0], [0x7, 0, 0, 0], [0x87, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['¬']   = [[0xE0, 0x38, 0, 0], [0x7, 0, 0, 0], [0x87, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['7']   = [[0x8, 0, 0, 0], [0x88, 0, 0, 0]];
    charmapES['/']   = [[0x2A, 0, 0, 0], [0x8, 0, 0, 0], [0x88, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['8']   = [[0x9, 0, 0, 0], [0x89, 0, 0, 0]];
    charmapES['(']   = [[0x2A, 0, 0, 0], [0x9, 0, 0, 0], [0x89, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['9']   = [[0x0A, 0, 0, 0], [0x8A, 0, 0, 0]];
    charmapES[')']   = [[0x2A, 0, 0, 0], [0x0A, 0, 0, 0], [0x8A, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['0']   = [[0x0B, 0, 0, 0], [0x8B, 0, 0, 0]];
    charmapES['=']   = [[0x2A, 0, 0, 0], [0x0B, 0, 0, 0], [0x8B, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['\'']  = [[0x0C, 0, 0, 0], [0x8C, 0, 0, 0]];
    charmapES['?']   = [[0x2A, 0, 0, 0], [0x0C, 0, 0, 0], [0x8C, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['¡']   = [[0x0D, 0, 0, 0], [0x8D, 0, 0, 0]];
    charmapES['¿']   = [[0x2A, 0, 0, 0], [0x0D, 0, 0, 0], [0x8D, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['q']   = [[0x10, 0, 0, 0], [0x90, 0, 0, 0]];
    charmapES['Q']   = [[0x2A, 0, 0, 0], [0x10, 0, 0, 0], [0x90, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['w']   = [[0x11, 0, 0, 0], [0x91, 0, 0, 0]];
    charmapES['W']   = [[0x2A, 0, 0, 0], [0x11, 0, 0, 0], [0x91, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['e']   = [[0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['E']   = [[0x2A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['€']   = [[0xE0, 0x38, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['r']   = [[0x13, 0, 0, 0], [0x93, 0, 0, 0]];
    charmapES['R']   = [[0x2A, 0, 0, 0], [0x13, 0, 0, 0], [0x93, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['t']   = [[0x14, 0, 0, 0], [0x94, 0, 0, 0]];
    charmapES['T']   = [[0x2A, 0, 0, 0], [0x14, 0, 0, 0], [0x94, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['y']   = [[0x15, 0, 0, 0], [0x95, 0, 0, 0]];
    charmapES['Y']   = [[0x2A, 0, 0, 0], [0x15, 0, 0, 0], [0x95, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['u']   = [[0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['U']   = [[0x2A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['i']   = [[0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['I']   = [[0x2A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['o']   = [[0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['O']   = [[0x2A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['p']   = [[0x19, 0, 0, 0], [0x99, 0, 0, 0]];
    charmapES['P']   = [[0x2A, 0, 0, 0], [0x19, 0, 0, 0], [0x99, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['`']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x39, 0, 0, 0], [0xb9, 0, 0, 0]];
    charmapES['à']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['À']   = [[0xAA, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x2A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['è']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['È']   = [[0xAA, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x2A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['ì']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['Ì']   = [[0xAA, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x2A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['ò']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['Ò']   = [[0xAA, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x2A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['ù']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['Ù']   = [[0xAA, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x2A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['â']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['Â']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['ê']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['Ê']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['î']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['Î']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['ô']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['Ô']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['û']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['Û']   = [[0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['^']   = [[0x2A, 0, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xAA, 0, 0, 0], [0x39, 0, 0, 0], [0xb9, 0, 0, 0]];
    charmapES['[']   = [[0xE0, 0x38, 0, 0], [0x1A, 0, 0, 0], [0x9A, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['+']   = [[0x1B, 0, 0, 0], [0x9B, 0, 0, 0]];
    charmapES['*']   = [[0x2A, 0, 0, 0], [0x1B, 0, 0, 0], [0x9B, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES[']']   = [[0xE0, 0x38, 0, 0], [0x1B, 0, 0, 0], [0x9B, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['a']   = [[0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['A']   = [[0x2A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['s']   = [[0x1F, 0, 0, 0], [0x9F, 0, 0, 0]];
    charmapES['S']   = [[0x2A, 0, 0, 0], [0x1F, 0, 0, 0], [0x9F, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['d']   = [[0x20, 0, 0, 0], [0xA0, 0, 0, 0]];
    charmapES['D']   = [[0x2A, 0, 0, 0], [0x20, 0, 0, 0], [0xA0, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['f']   = [[0x21, 0, 0, 0], [0xA1, 0, 0, 0]];
    charmapES['F']   = [[0x2A, 0, 0, 0], [0x21, 0, 0, 0], [0xA1, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['g']   = [[0x22, 0, 0, 0], [0xA2, 0, 0, 0]];
    charmapES['G']   = [[0x2A, 0, 0, 0], [0x22, 0, 0, 0], [0xA2, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['h']   = [[0x23, 0, 0, 0], [0xA3, 0, 0, 0]];
    charmapES['H']   = [[0x2A, 0, 0, 0], [0x23, 0, 0, 0], [0xA3, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['j']   = [[0x24, 0, 0, 0], [0xA4, 0, 0, 0]];
    charmapES['J']   = [[0x2A, 0, 0, 0], [0x24, 0, 0, 0], [0xA4, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['k']   = [[0x25, 0, 0, 0], [0xA5, 0, 0, 0]];
    charmapES['K']   = [[0x2A, 0, 0, 0], [0x25, 0, 0, 0], [0xA5, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['l']   = [[0x26, 0, 0, 0], [0xA6, 0, 0, 0]];
    charmapES['L']   = [[0x2A, 0, 0, 0], [0x26, 0, 0, 0], [0xA6, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['ñ']   = [[0x27, 0, 0, 0], [0xA7, 0, 0, 0]];
    charmapES['Ñ']   = [[0x2A, 0, 0, 0], [0x27, 0, 0, 0], [0xA7, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['á']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['Á']   = [[0xAA, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x2A, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['é']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['É']   = [[0xAA, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x2A, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['í']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['Í']   = [[0xAA, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x2A, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['ó']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['Ó']   = [[0xAA, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x2A, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['ú']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['Ú']   = [[0xAA, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x2A, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['ä']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['Ä']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x1E, 0, 0, 0], [0x9E, 0, 0, 0]];
    charmapES['ë']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['Ë']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x12, 0, 0, 0], [0x92, 0, 0, 0]];
    charmapES['ï']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['Ï']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x17, 0, 0, 0], [0x97, 0, 0, 0]];
    charmapES['ö']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['Ö']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x18, 0, 0, 0], [0x98, 0, 0, 0]];
    charmapES['ü']   = [[0x2A, 0, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xAA, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['Ü']   = [[0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0x16, 0, 0, 0], [0x96, 0, 0, 0]];
    charmapES['{']   = [[0xE0, 0x38, 0, 0], [0x28, 0, 0, 0], [0xA8, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['ç']   = [[0x2B, 0, 0, 0], [0xAB, 0, 0, 0]];
    charmapES['Ç']   = [[0x2A, 0, 0, 0], [0x2B, 0, 0, 0], [0xAB, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['}']   = [[0xE0, 0x38, 0, 0], [0x2B, 0, 0, 0], [0xAB, 0, 0, 0], [0xE0, 0xB8, 0, 0]];
    charmapES['<']   = [[0x56, 0, 0, 0], [0xD6, 0, 0, 0]];
    charmapES['>']   = [[0x2A, 0, 0, 0], [0x56, 0, 0, 0], [0xD6, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['z']   = [[0x2C, 0, 0, 0], [0xAC, 0, 0, 0]];
    charmapES['Z']   = [[0x2A, 0, 0, 0], [0x2C, 0, 0, 0], [0xAC, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['x']   = [[0x2D, 0, 0, 0], [0xAD, 0, 0, 0]];
    charmapES['X']   = [[0x2A, 0, 0, 0], [0x2D, 0, 0, 0], [0xAD, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['c']   = [[0x2E, 0, 0, 0], [0xAE, 0, 0, 0]];
    charmapES['C']   = [[0x2A, 0, 0, 0], [0x2E, 0, 0, 0], [0xAE, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['v']   = [[0x2F, 0, 0, 0], [0xAF, 0, 0, 0]];
    charmapES['V']   = [[0x2A, 0, 0, 0], [0x2F, 0, 0, 0], [0xAF, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['b']   = [[0x30, 0, 0, 0], [0xB0, 0, 0, 0]];
    charmapES['B']   = [[0x2A, 0, 0, 0], [0x30, 0, 0, 0], [0xB0, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['n']   = [[0x31, 0, 0, 0], [0xB1, 0, 0, 0]];
    charmapES['N']   = [[0x2A, 0, 0, 0], [0x31, 0, 0, 0], [0xB1, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['m']   = [[0x32, 0, 0, 0], [0xB2, 0, 0, 0]];
    charmapES['M']   = [[0x2A, 0, 0, 0], [0x32, 0, 0, 0], [0xB2, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES[',']   = [[0x33, 0, 0, 0], [0xB3, 0, 0, 0]];
    charmapES[';']   = [[0x2A, 0, 0, 0], [0x33, 0, 0, 0], [0xB3, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['.']   = [[0x34, 0, 0, 0], [0xB4, 0, 0, 0]];
    charmapES[':']   = [[0x2A, 0, 0, 0], [0x34, 0, 0, 0], [0xB4, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES['-']   = [[0x35, 0, 0, 0], [0xB5, 0, 0, 0]];
    charmapES['_']   = [[0x2A, 0, 0, 0], [0x35, 0, 0, 0], [0xB5, 0, 0, 0], [0xAA, 0, 0, 0]];
    charmapES[' ']   = [[0x39, 0, 0, 0], [0xb9, 0, 0, 0]];

    // keyboard keys without character associated.
    // all the js events associated to these keys should have a keyChar associated
    var keymapES = [];

    keymapES[27]                 = 0x1; // ESC
    keymapES[9]                 = 0x0F; // TAB
    //keymapES[20]                = 0x3A; // BLOQ.MAY. => see the charmap, all the capital letters and shift chars send a shift in their sequence
    keymapES[16]                = 0x2A; // LEFT SHIFT and RIGHT SHIFT
	keymapES[91]                = 0x1D; // LEFT GUI (META, COMMAND) BINDED TO CONTROL
	keymapES[17]                = 0x1D; // LEFT CONTROL and RIGHT CONTROL
    //keymapES[32]                = 0x39; // SPACE => see the charmap
    keymapES[8]                 = 0x0E; // BACKSPACE
    keymapES[13]                = 0x1C; // ENTER
    //keymapES[225]                 = 0x38; // RIGHT ALT (ALT GR) => see the charmap, all the altgr chars send a altgr in their sequence
    keymapES[18]                = 0x38; // LEFT ALT
  // keymapES[92]                = 0x5C; // RIGHT GUI (WINDOWS)
    keymapES[38]                = 0x48; // UP ARROW
    keymapES[37]                = 0x4B; // LEFT ARROW
    keymapES[40]                = 0x50; // DOWN ARROW
    keymapES[39]                = 0x4D; // RIGHT ARROW
    keymapES[45]                = 0x52; // INSERT
    keymapES[46]                = 0x53; // DELETE
    keymapES[36]                = 0x47; // HOME
    keymapES[35]                = 0x4F; // FIN
    keymapES[33]                = 0x49; // PAGE UP
    keymapES[34]                = 0x51; // PAGE UP
    keymapES[144]               = 0x45; // BLOQ.NUM.
    keymapES[145]                = 0x46; // SCROLL LOCK
    keymapES[112]                = 0x3B; // F1
    keymapES[113]                = 0x3C; // F2
    keymapES[114]                = 0x3D; // F3
    keymapES[115]                = 0x3E; // F4
    keymapES[116]                = 0x3F; // F5
    keymapES[117]                = 0x40; // F6
    keymapES[118]                = 0x41; // F7
    keymapES[119]                = 0x42; // F8
    keymapES[120]                = 0x43; // F9
    keymapES[121]                = 0x44; // F10
    keymapES[122]                = 0x57; // F11
    keymapES[123]                = 0x58; // F12

    // combination keys with ctrl
    var ctrlKeymapES = [];

    ctrlKeymapES[65]                = 0x1E; // a
    ctrlKeymapES[81]                = 0x10; // q
    ctrlKeymapES[87]                = 0x11; // w
    ctrlKeymapES[69]                = 0x12; // e
    ctrlKeymapES[82]                = 0x13; // r
    ctrlKeymapES[84]                = 0x14; // t
    ctrlKeymapES[89]                = 0x15; // y
    ctrlKeymapES[85]                = 0x16; // u
    ctrlKeymapES[73]                = 0x17; // i
    ctrlKeymapES[79]                = 0x18; // o
    ctrlKeymapES[80]                = 0x19; // p
    ctrlKeymapES[65]                = 0x1E; // a
    ctrlKeymapES[83]                = 0x1F; // s
    ctrlKeymapES[68]                = 0x20; // d
    ctrlKeymapES[70]                = 0x21; // f
    ctrlKeymapES[71]                = 0x22; // g
    ctrlKeymapES[72]                = 0x23; // h
    ctrlKeymapES[74]                = 0x24; // j
    ctrlKeymapES[75]                = 0x25; // k
    ctrlKeymapES[76]                = 0x26; // l
    ctrlKeymapES[90]                = 0x2C; // z
    ctrlKeymapES[88]                = 0x2D; // x
    ctrlKeymapES[67]                = 0x2E; // c
    //ctrlKeymapES[86]                = 0x2F; // v      to enable set disableClipboard = true in run.js
    ctrlKeymapES[66]                = 0x30; // b
    ctrlKeymapES[78]                = 0x31; // n
    ctrlKeymapES[77]                = 0x32; // m

    // reserved ctrl+? combinations we want to intercept from browser and inject manually to spice
    var reservedCtrlKeymap = [];
    reservedCtrlKeymap[86] = 0x2F;

    return {
        getKeymap: function() {
            return keymapES;
        },

        getCtrlKeymap: function() {
            return ctrlKeymapES;
        },

        getReservedCtrlKeymap: function() {
            return reservedCtrlKeymap;
        },

        getCharmap: function() {
            return charmapES;
        },

        setCtrlKey: function (key, val) {
            ctrlKeymapES[key] = val;
        }
    };
}( );
