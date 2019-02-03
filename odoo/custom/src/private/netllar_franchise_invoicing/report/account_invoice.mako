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

    td.events {
        text-align: center;
        font-size: 7px;
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
            import collections
            groups = collections.OrderedDict()
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
                                <tr><td>${inv.partner_id.commercial_partner_id.street or ''}</td></tr>
                                %if inv.partner_id.commercial_partner_id.street2:
                                    <tr><td>${inv.partner_id.commercial_partner_id.street2 or ''}</td></tr>
                                %endif
                                <tr><td>${inv.partner_id.commercial_partner_id.zip or ''} ${inv.partner_id.commercial_partner_id.city or ''}
                                %if inv.partner_id.commercial_partner_id.country_id:
                                    (${inv.partner_id.commercial_partner_id.country_id.name or ''})
                                %endif
                                </td></tr>
                                <tr><td>NIF: ${inv.partner_id.commercial_partner_id.vat and inv.partner_id.commercial_partner_id.vat.upper().replace('ES', '') or ''}</td></tr>
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
                    <td>${inv.partner_id.commercial_partner_id.id or ''}</td>
                    <td>${inv.name or ''}</td>
                </tr>
            </table>

            <%
            hay_descuentos = False
            columnas_descripcion = 3
            for line in inv.invoice_line :
                if line.discount <> 0:
                    hay_descuentos = True
                    columnas_descripcion = 2
            %>

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
                %if inv.payment_mode_id and inv.payment_mode_id.name.startswith('Recibo domiciliado'):
                    Se realizará el cargo en la siguiente cuenta:<br>
                    %for bank_line in inv.partner_id.bank_ids:
                        %if len(inv.partner_id.bank_ids) == 1 or bank_line.default_bank:
                            ${(bank_line.bank_name and (bank_line.bank_name) + ' - ' or '') + bank_line.acc_number[0:10] + ' ** ' + bank_line.acc_number[13:15] + '******' + bank_line.acc_number[-2:]}
                        %endif
                    %endfor
                %else:
                    ${ inv.payment_mode_id.note or inv.payment_mode_id.name }
                %endif
                <br>
		        <br>
                %if inv.move_id:
                    <b>Vencimientos</b><br>
                    %if inv.payment_mode_id and inv.payment_mode_id.name.startswith('Recibo domiciliado'):
                        Cargo en cuenta a partir fecha indicada:<br>
                    %endif
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
                    <%
                    total_minutos_llamadas = 0
                    total_importe_llamadas = 0
                    total_volumen_datos = 0
                    total_importe_datos = 0
                    total_sms = 0
                    total_importe_sms = 0
                    duracion_llamadas = ""
                    %>
                    <h3>Detalle de consumos del número ${caller_id and caller_id.name or ''}</h3>
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
                                        %if cdr_line.line_type == 'data':
                                            <% total_volumen_datos = total_volumen_datos + duracion %>
                                            <% total_importe_datos = total_importe_datos + cdr_line.price %>
                                        %else:
                                            %if cdr_line.line_type in ['call', 'call_roaming']:
                                                <% total_minutos_llamadas = total_minutos_llamadas + cdr_line.length %>
                                                <% total_importe_llamadas = total_importe_llamadas + cdr_line.price %>
                                                %if (duracion / 3600) >= 1:
                                                    <% length = str(int(duracion/3600)) + "h" %>
                                                    <% duracion = duracion % 3600 %>
                                                %endif
                                                %if (duracion / 60) >= 1:
                                                    <% length += str(int(duracion/60)) + "m" %>
                                                    <% duracion = duracion % 60 %>
                                                %endif
                                                <% length += str(duracion) + "s" %>
                                            %elif cdr_line.line_type == 'data_roaming':
                                                <% total_volumen_datos = total_volumen_datos + duracion %>
                                                <% total_importe_datos = total_importe_datos + cdr_line.price %>
                                                <% length = str(duracion) + "kB" %>
                                            %elif cdr_line.line_type in ['sms', 'sms_roaming']:
                                                <% total_sms = total_sms + 1 %>
                                                <% total_importe_sms = total_importe_sms + cdr_line.price %>
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
                                        %endif
                                    %endfor
                                </tr>
                            </tr>
                        </tbody>
                    </table>

                    <% duracion = total_minutos_llamadas %>
                    %if (duracion / 3600) >= 1:
                        <% duracion_llamadas = str(int(duracion/3600)) + "h " %>
                        <% duracion = duracion % 3600 %>
                    %endif
                    %if (duracion / 60) >= 1:
                        <% duracion_llamadas += str(int(duracion/60)) + "m " %>
                        <% duracion = duracion % 60 %>
                    %endif
                    <% duracion_llamadas += str(duracion) + "s" %>
                    <h4>
                    <table>
                        <tr><td>Duración total de las llamadas:</td><td>${duracion_llamadas}</td></tr>
                        <tr><td>Importe de las llamadas:</td><td>${formatLang(total_importe_llamadas, digits=2)} ${inv.currency_id.symbol}</td></tr>
                        % if caller_id.type == 'mobile':
                            <tr><td>Volumen total de datos consumidos:</td><td>${total_volumen_datos/1024} MB</td></tr>
                            <tr><td>Importe de datos consumidos:</td><td>${formatLang(total_importe_datos, digits=2)} ${inv.currency_id.symbol}</td></tr>
                            % if total_sms>0:
                                <tr><td>SMS enviados:</td><td>${total_sms}</td></tr>
                                <tr><td>Importe de SMS:</td><td>${formatLang(total_importe_sms, digits=2)} ${inv.currency_id.symbol}</td></tr>
                            %endif
                        %endif
                    </table>
                    </h4>
                %endfor
            %endif

            %if inv.franchise_line:
                <%
                    def get_call_length_string(duracion):
                        length = ""
                        if (duracion / 3600) >= 1:
                            length = str(int(duracion / 3600)) + "h"
                            duracion %= 3600
                        if (duracion / 60) >= 1:
                            length += str(int(duracion / 60)) + "m"
                            duracion %= 60
                        length += str(duracion) + "s"
                        return length
                %>
                <p style="page-break-after:always"></p>
                <br/>
                <%
                cli_groups = groupRecord(inv.franchise_line, 'caller_id')
                %>
                <h2>Detalle de llamadas de los abonados de la franquicia</h2>
                    
                    <table width="100%" style="border-collapse:collapse;">
                        <theader>
                            <th style="width:7%;text-align:center;font-size:8px;">Nº Abonado</th>
                            <th style="width:8%;text-align:center;font-size:8px;">Voz</th>
                            <th style="width:11%;text-align:center;font-size:8px;">Datos</th>
                            <th style="width:6%;text-align:center;font-size:8px;">SMS/MMS</th>
                            <th style="width:15%;text-align:center;font-size:8px;">Roaming</th>
                            <th style="width:7%;text-align:center;font-size:8px;">Nº Abonado</th>
                            <th style="width:8%;text-align:center;font-size:8px;">Voz</th>
                            <th style="width:11%;text-align:center;font-size:8px;">Datos</th>
                            <th style="width:6%;text-align:center;font-size:8px;">SMS/MMS</th>
                            <th style="width:15%;text-align:center;font-size:8px;">Roaming</th>
                        </theader>
                        <tr>
                <% i = 0 %>
                %for caller_id, franchise_lines in cli_groups.iteritems():
                    <%
                        total_llamadas_fr = 0
                        importe_llamadas_fr = 0
                        total_datos_fr = 0
                        importe_datos_fr = 0
                        total_sms_fr = 0
                        importe_sms_fr = 0
                        importe_roaming_fr = 0
                    %>
                                    %for franchise_line in franchise_lines:
                                        <%
                                            cdr_line = franchise_line.cdr_line_id
                                            length = ""
                                            duracion = cdr_line.length
                                            if cdr_line.line_type in ['call']:
                                                length = get_call_length_string(duracion)
                                                total_llamadas_fr += cdr_line.length
                                                importe_llamadas_fr += franchise_line.price
                                            elif cdr_line.line_type in ['data']:
                                                length = "%skB" % duracion
                                                total_datos_fr += cdr_line.length
                                                importe_datos_fr += franchise_line.price
                                            elif cdr_line.line_type in ['sms']:
                                                total_sms_fr += cdr_line.length
                                                importe_sms_fr += franchise_line.price
                                            elif cdr_line.line_type in ['call_roaming', 'data_roaming', 'mms_roaming', 'sms_roaming']:
                                                importe_roaming_fr += franchise_line.price
                                        %>
                                        %if cdr_line.line_type == 'data' or not cdr_line.length or not franchise_line.price:
                                            <% continue %>
                                        %endif
                                    %endfor
                                    <td class="events">${caller_id.name}</td>
                                    <td class="events">${get_call_length_string(total_llamadas_fr)} | ${formatLang(importe_llamadas_fr, digits=2)} ${inv.currency_id.symbol}</td>
                                    <td class="events">${round(total_datos_fr / 1024, 2)} MB | ${formatLang(importe_datos_fr, digits=2)} ${inv.currency_id.symbol}</td>
                                    <td class="events">${total_sms_fr} | ${formatLang(importe_sms_fr, digits=2)} ${inv.currency_id.symbol}</td>
                                    <td class="events">${formatLang(importe_roaming_fr, digits=2)} ${inv.currency_id.symbol}</td>
                                    %if i % 2 == 1:
                                         </tr><tr>
                                    %endif
                                <% i += 1 %>
                                %endfor
                    </table>
            %endif

            %if inv != objects[-1]:
                <p style="page-break-after:always"></p>
            %endif
        %endfor
    </body>
    </html>
