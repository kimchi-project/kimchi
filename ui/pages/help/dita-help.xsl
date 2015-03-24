<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns="http://www.w3.org/1999/xhtml">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />

    <xsl:template match="/">
        <html>
            <head>
                <title><xsl:value-of select="/cshelp/title" /></title>
                <meta charset="UTF-8" />
                <link rel="shortcut icon" href="../../images/logo.ico" />
                <link rel="stylesheet" type="text/css" href="../kimchi.css" />
            </head>
            <body>
                <xsl:apply-templates select="//cshelp" />
            </body>
        </html>
    </xsl:template>

    <xsl:template match="cshelp">
        <h1><xsl:value-of select="title" /></h1>
        <p class="shortdesc"><xsl:value-of select="shortdesc" /></p>
        <p class="csbody"><xsl:copy-of select="csbody/node()" /></p>
    </xsl:template>
</xsl:stylesheet>
