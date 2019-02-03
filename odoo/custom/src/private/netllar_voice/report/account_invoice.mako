    <html>
    <head>
        <style type="text/css">
            ${css}
    
    .list_invoice_table {
        border:thin solid #E3E4EA;
        text-align:center;
        border-collapse: collapse;
    }
    .list_invoice_table th {
        background-color: #EEEEEE;
        border: thin solid #000000;
        text-align:center;
        font-size:12;
        font-weight:bold;
        padding-right:3px;
        padding-left:3px;
    }
    .list_invoice_table td {
        border-top : thin solid #EEEEEE;
        text-align:left;
        font-size:12;
        padding-right:3px;
        padding-left:3px;
        padding-top:3px;
        padding-bottom:3px;
    }
    .list_invoice_table thead {
        display:table-header-group;
    }
    
    
    .list_bank_table {
        text-align:center;
        border-collapse: collapse;
    }
    .list_bank_table th {
        background-color: #EEEEEE;
        text-align:left;
        font-size:12;
        font-weight:bold;
        padding-right:3px;
        padding-left:3px;
    }
    .list_bank_table td {
        text-align:left;
        font-size:12;
        padding-right:3px;
        padding-left:3px;
        padding-top:3px;
        padding-bottom:3px;
    }
    
    
    .list_tax_table {
    }
    .list_tax_table td {
        text-align:left;
        font-size:12;
    }
    .list_tax_table th {
    }
    .list_tax_table thead {
        display:table-header-group;
    }
    
    
    .list_total_table {
        border:thin solid #E3E4EA;
        text-align:center;
        border-collapse: collapse;
    }
    .list_total_table td {
        border-top : thin solid #EEEEEE;
        text-align:left;
        font-size:12;
        padding-right:3px;
        padding-left:3px;
        padding-top:3px;
        padding-bottom:3px;
    }
    .list_total_table th {
        background-color: #EEEEEE;
        border: thin solid #000000;
        text-align:center;
        font-size:12;
        font-weight:bold;
        padding-right:3px
        padding-left:3px
    }
    .list_total_table thead {
        display:table-header-group;
    }
    
    
    .no_bloc {
        border-top: thin solid  #ffffff ;
    }
    
    .right_table {
        right: 4cm;
        width:"100%";
    }
    
    .std_text {
        font-size:12;
    }
    
    td.amount {
        text-align: right;
        white-space: nowrap;
    }
    
    tfoot.totals tr:first-child td{
        padding-top: 15px;
    }
    
    th.date {
        width: 90px;
    }
    
    td.date {
        white-space: nowrap;
        width: 90px;
    }
    
    td.vat {
        white-space: nowrap;
    }
    
        </style>
    </head>
    <body>
        <%
        def groupRecord(records, field):
            groups = {}
            for record in records:
                if record[field] in groups:
                    groups[record[field]].append(record)
                else:
                    groups[record[field]] = [record]
            return groups
        %>
        <%page expression_filter="entity"/>
        <%
        def carriage_returns(text):
            return text.replace('\n', '<br />')
        %>
    
        %for inv in objects:
            <% setLang(inv.partner_id.lang) %>
            <div class="address">
                <table width="100%" border="0">
                    <tr><td colspan="4" height="30">&nbsp;</td></tr>
                    <tr>
                        <td width="40%">&nbsp;</td>
                        <td width="45%" class="recipient">
                            <table class="recipient">
                                <tr><td class="name">${inv.partner_id.title and inv.partner_id.title.name or ''} ${inv.partner_id.name }</td></tr>
                                <tr><td>${inv.partner_id.street or ''}</td></tr>
                                %if inv.partner_id.street2:
                                    <tr><td>${inv.partner_id.street2 or ''}</td></tr>
                                %endif
                                <tr><td>${inv.partner_id.zip or ''} ${inv.partner_id.city or ''}
                                %if inv.partner_id.country_id:
                                    (${inv.partner_id.country_id.name or ''})
                                %endif
                                </td></tr>
                                <tr><td>NIF: ${inv.partner_id.vat and inv.partner_id.vat.upper().replace('ES', '') or ''}</td></tr>
                            </table>
                        </td>
                        <td width="5%"></td>
                    <tr>
                </table>
            </div>
            <h1 style="clear: both; padding-top: 20px;">
                %if inv.type == 'out_invoice' and inv.state == 'proforma2':
                    ${_("PRO-FORMA")}
                %elif inv.type == 'out_invoice' and inv.state == 'draft':
                    ${_("Draft Invoice")}
                %elif inv.type == 'out_invoice' and inv.state == 'cancel':
                    ${_("Cancelled Invoice")} ${inv.number or ''}
                %elif inv.type == 'out_invoice':
                    ${_("Invoice")} ${inv.number or ''}
                %elif inv.type == 'in_invoice':
                    ${_("Supplier Invoice")} ${inv.number or ''}
                %elif inv.type == 'out_refund':
                    ${_("Refund")} ${inv.number or ''}
                %elif inv.type == 'in_refund':
                    ${_("Supplier Refund")} ${inv.number or ''}
                %endif
            </h1>
            <table class="basic_table" width="100%">
                <tr>
                    <th class="date" width="20%">${_("Invoice Date")}</th>
                    <th width="20%">Origen</th>
                    <th width="20%">Código de cliente</th>
                    <th width="40%">Descripción</th>
                </tr>
                <tr>
                    <td class="date">${formatLang(inv.date_invoice, date=True)}</td>
                    <td>${inv.origin or ''}</td>
                    <td>${inv.partner_id.id or ''}</td>
                    <td>${inv.name or ''}</td>
                </tr>
            </table>
            
            <%  hay_descuentos = False %>
            <%  columnas_descripcion = 3 %>
            %for line in inv.invoice_line :
                %if line.discount <> 0:
                    <% hay_descuentos = True %>
                    <% columnas_descripcion = 2 %>
                %endif
            %endfor
            
            <table class="list_invoice_table" width="100%" style="margin-top: 20px;">
                <thead>
                    <tr>
                        <th colspan="${columnas_descripcion}">${_("Description")}</th>
                        <th nowrap>Cantidad</th>
                        <th nowrap>${_("Unit Price")}</th>
                        %if hay_descuentos:
                        <th nowrap>${_("Disc.(%)")}</th>
                        %endif
                        <th nowrap>Precio</th>
                    </tr>
                </thead>
                <tbody>
                %for line in inv.invoice_line :
                    <tr>
                        <td colspan="${columnas_descripcion}">${line.name}</td>
                        <td class="amount" width="10%" nowrap>${formatLang(line.quantity or 0.0,digits=get_digits(dp='Account'))} ${line.uos_id and line.uos_id.name or ''}</td>
                        <td class="amount" width="10%" nowrap>${formatLang(line.price_unit)}</td>
                        %if hay_descuentos:
                        <td class="amount" width="10%" nowrap>${formatLang(line.discount, digits=get_digits(dp='Account'))}%</td>
                        %endif
                        <td class="amount" width="10%" nowrap>${formatLang(line.price_subtotal, digits=get_digits(dp='Account'))} ${inv.currency_id.symbol}</td>
                    </tr>
                    %if line.note:
                        <tr>
                            <td colspan="6" class="note" style="font-style:italic;font-size:10;border-top:thin solid  #ffffff;">${line.note | carriage_returns}</td>
                        </tr>
                    %endif
                %endfor
                </tbody>
                <tfoot class="totals">
                    <tr>
                        <td colspan="5" style="text-align:right;border-right: thin solid  #ffffff ;border-left: thin solid  #ffffff ;">
                            <b>Base:</b>
                        </td>
                        <td class="amount" style="border-right: thin solid  #ffffff ;border-left: thin solid  #ffffff ;">
                            ${formatLang(inv.amount_untaxed, digits=get_digits(dp='Account'))} ${inv.currency_id.symbol}
                        </td>
                    </tr>
                    <tr class="no_bloc">
                        <td colspan="5" style="text-align:right; border-top: thin solid  #ffffff ; border-right: thin solid  #ffffff ;border-left: thin solid  #ffffff ;">
                            <b>${_("Taxes:")}</b>
                        </td>
                        <td class="amount" style="border-right: thin solid  #ffffff ;border-top: thin solid  #ffffff ;border-left: thin solid  #ffffff ;">
                                ${formatLang(inv.amount_tax, digits=get_digits(dp='Account'))} ${inv.currency_id.symbol}
                        </td>
                    </tr>
                    <tr>
                        <td colspan="4" style="border-right: thin solid  #ffffff ;border-top: thin solid  #ffffff ;border-bottom: thin solid  #ffffff ;border-left: thin solid  #ffffff ;"></td>
                        <td class="total" style="text-align:right;font-size: 14px;">
                            ${_("Total:")}
                        </td>
                        <td class="total" style="text-align:right;font-size: 14px;" nowrap>&nbsp;&nbsp;
                            ${formatLang(inv.amount_total, digits=get_digits(dp='Account'))} ${inv.currency_id.symbol}
                        </td>
                    </tr>
                </tfoot>
            </table>
                <br/> <br/> <br/>
            <table class="list_total_table" width="40%" >
                <tr>
                    <th>Impuesto</th>
                    <th>${_("Base")}</th>
                    <th>${_("Tax")}</th>
                </tr>
                %if inv.tax_line:
                    %for t in inv.tax_line:
                        <tr>
                            <td style="text-align:center;" nowrap>${ t.name } </td>
                            <td style="text-align:center;" nowrap>${ formatLang(t.base, digits=get_digits(dp='Account')) } ${inv.currency_id.symbol}</td>
                            <td style="text-align:center;" nowrap>${ formatLang(t.amount, digits=get_digits(dp='Account')) } ${inv.currency_id.symbol}</td>
                        </tr>
                    %endfor
                %endif
            </table>
            %if inv.type == 'out_invoice':
                <br/> <br/> <br/>
                <b>Forma de pago</b><br>
                %if inv.payment_type and inv.payment_type.code.startswith('RECIBO_CSB'):
                    Se realizará el cargo en la siguiente cuenta:<br>
                    %for bank_line in inv.partner_id.bank_ids:
                        %if bank_line.default_bank or len(inv.partner_id.bank_ids) == 1:
                            ${(bank_line.bank_name and (bank_line.bank_name) + ' - ' or '') + bank_line.acc_number[0:10] + ' ** ' + bank_line.acc_number[13:15] + '******' + bank_line.acc_number[-2:]}<br>
                        %endif
                    %endfor
                %endif
                <br>
                %if inv.move_id:
                    <b>Vencimientos</b><br>
                    %for move_line in inv.move_id.line_id:
                        %if move_line.account_id.type == 'receivable':
                            ${move_line.date_maturity} - ${formatLang(abs(move_line.debit - move_line.credit), digits=get_digits(dp='Account'))} ${inv.currency_id.symbol}<br>
                        %endif
                    %endfor
                %endif
            %endif
            <br>
            <hr/>
            <p style="font-size:7px;text-align: justify;">De acuerdo con lo establecido por la Ley Orgánica 15/1999, de 13 de Diciembre, de Protección de Datos de Carácter Personal (LOPD), le informamos que sus datos están incorporados en un fichero del que es titular ${inv.company_id.name} con NIF ${inv.company_id.vat.replace('ES', '')} con la finalidad de: Realizar la gestión administrativa, contable y fiscal, así como enviarle comunicaciones comerciales sobre nuestros productos y/o servicios, asimismo le informamos de la posibilidad de ejercer los derechos de acceso, rectificación, cancelación y oposición de sus datos en el domicilio ${inv.company_id.partner_id.street} - ${inv.company_id.partner_id.zip} ${inv.company_id.partner_id.city} (${inv.company_id.partner_id.state_id.name}).<br>Usted puede solicitar la recepción de las facturas en papel comunicándonoslo por escrito.</p>
            %if inv.comment:
                <br/>
                <p class="std_text">${inv.comment | carriage_returns}</p>
            %endif
            %if inv.cdr_line:
                <p style="page-break-after:always"></p>
                <br/>
                <%
                cli_groups = groupRecord(inv.cdr_line, 'caller_id')
                %>
                %for caller_id, cdr_lines in cli_groups.iteritems():
                    <h3>Detalle de llamadas ${caller_id and caller_id.name or ''}</h3>
                    <table width="100%" style="border-collapse:collapse;">
                        <theader>
                            <th style="width:14%;text-align:center;font-size:8px;">Fecha</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Tipo</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Nº destino</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Duración</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Precio</th>
                            <th style="width:14%;text-align:center;font-size:8px;">Fecha</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Tipo</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Nº destino</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Duración</th>
                            <th style="width:9%;text-align:center;font-size:8px;">Precio</th>
                        </theader>
                        <tbody>
                            <tr>
                                <tr>
                                    <% i = 0 %>
                                    %for cdr_line in cdr_lines:
                                        <% length = "" %>
                                        <% duracion = cdr_line.length %>
                                        %if cdr_line.line_type == 'call':
                                            %if (duracion / 3600) >= 1:
                                                <% length = int((duracion/3600)) + "h" %>
                                                <% duracion = duracion % 3600 %>
                                            %endif
                                            %if (duracion / 60) >= 1:
                                                <% length += str(int(duracion/60)) + "m" %>
                                                <% duracion = duracion % 60 %>
                                            %endif
                                            <% length += str(duracion) + "s" %>
                                        %elif cdr_line.line_type == 'data':
                                            <% length = "%skB" % duracion %>
                                        %endif
                                        <td style="font-size:7px;text-align:center;">${cdr_line.date}</td>
                                        <td style="font-size:7px;text-align:center;">${_(cdr_line.line_type)}</td>
                                        <td style="font-size:7px;text-align:center;">${cdr_line.dest or '-'}</td>
                                        <td style="font-size:7px;text-align:center;">${length}</td>
                                        %if i % 2 == 1:
                                             <td style="font-size:7px;text-align:center;">${formatLang(cdr_line.price, digits=4)} ${inv.currency_id.symbol}</td>
                                            </tr>
                                        %else:
                                             <td style="font-size:7px;text-align:center;border-width:thin;border-right-style:solid;border-color:grey;">${formatLang(cdr_line.price, digits=4)} ${inv.currency_id.symbol}</td>
                                        %endif
                                        <% i += 1 %>
                                    %endfor
                                </tr>
                            </tr>
                        </tbody>
                    </table>
                %endfor
            %endif
            %if inv != objects[-1]:
                <p style="page-break-after:always"></p>
            %endif
        %endfor
    </body>
    </html>
