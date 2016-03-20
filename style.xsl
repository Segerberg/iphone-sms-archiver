<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<xsl:apply-templates/>
</xsl:template>
<xsl:template match="conversation">
<html>
<style>
body {
    background: none repeat scroll 0 0 #fff;
    color: #FFFFFF;
    font-family: "helvetica neue";
    line-height: 26px;
    width: 400px;
    margin: 0 auto;
    overflow-X: hidden;
    position: relative;
}

.messages-wrapper {
  padding-top: 10px;
  position: relative;
  border: 1px solid #ddd;
  border-top: 0 none;
}
.message {
    border-radius: 20px 20px 20px 20px;
    margin: 0 15px 10px;
    padding: 15px 20px;
    position: relative;
}
.message.to {
    background-color: #2095FE;
    color: #fff;
    margin-left: 80px;
}
.message.from {
    background-color: #E5E4E9;
    color: #363636;
    margin-right: 80px;
}
.message.to + .message.to,
.message.from + .message.from {
  margin-top: -7px;
}
.message:before {
    border-color: #2095FE;
    border-radius: 50% 50% 50% 50%;
    border-style: solid;
    border-width: 0 20px;
    bottom: 0;
    clip: rect(20px, 35px, 42px, 0px);
    content: " ";
    height: 40px;
    position: absolute;
    right: -50px;
    width: 30px;
    z-index: -1;
}
.message.from:before {
    border-color: #E5E4E9;
    left: -50px;
    transform: rotateY(180deg);
}
.name {
    
    color: #363636;
    font-size: 10px;
    left: -50px;
}
</style>
<body>
    <xsl:for-each select="message">
    <center><div class="name">
    <xsl:value-of select="from/fname"/>&#160;
    <xsl:value-of select="from/sname"/>&#160;
    <xsl:value-of select="datetime"/>
    </div>
    </center>
      <xsl:if test="@isFromMe = '1'">
          <div class="message to">
          <xsl:value-of select="text"/>
        <xsl:if test="(attachment)">
        <xsl:variable name="link" select="attachment/@file"/>
        <img src="attachments/{$link}" height="150" width="150"/>
        </xsl:if> 
    </div>   
      </xsl:if>
      <xsl:if test="@isFromMe = '0'">  
          <div class="message from">
          <xsl:value-of select="text"/>
            <xsl:if test="(attachment)">
        <xsl:variable name="link" select="attachment/@file"/>
        <img src="attachments/{$link}" height="150" width="150"/>
        </xsl:if>
          </div>
      </xsl:if>   
    </xsl:for-each>
  </body> 
 </html> 
</xsl:template>
</xsl:stylesheet>
