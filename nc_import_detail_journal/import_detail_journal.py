# -*- coding: utf-8 -*-


from asyncio.windows_events import NULL
import time
from datetime import datetime
import tempfile
import binascii
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import logging
import xlrd
_logger = logging.getLogger(__name__)


import os
from io import BytesIO
from odoo.tools.misc import xlwt
import io
import base64
from xlwt import easyxf





# class Import_detail_journal(models.Model):
#     #_inherit = 'account.move'    

#     File_slect = fields.Binary(string="Select Excel File")
#     prueba=fields.Char('Report_Name')



    

#     def import_file(self): 
#     # -----------------------------
#      try:
#         fp= tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
#         fp.write(binascii.a2b_base64(self.File_slect))
#         fp.seek(0)
#         values = {}
#         workbook = xlrd.open_workbook(fp.name)
#         #sheet = workbook.sheet_by_name("Hoja1")
#         sheet = workbook.sheet_by_index(0)   
#         #saber cantidad de fils  sheet.nrows
        

#      except:
#             raise UserError(_("Invalid file!"))
     
#      self.ref=sheet.cell_value(0,0)
#      self.prueba=fp.name

#      for i in range(sheet.nrows):
#       if i >=2 :
#         for l in self: 
#          cuenta=sheet.cell_value(i,0)
#          id_cuenta = self.env['account.account'].search([('code','=',cuenta)]) 
#          moneda=sheet.cell_value(i,1)  
#          currency_id= self.env['res.currency'].search([('name','=',moneda)])  
#          amount_currency= sheet.cell_value(i,2)
#          debito=sheet.cell_value(i,3)
#          credito=sheet.cell_value(i,4)
#          self.ref=amount_currency                       
#          line = ({'account_id': id_cuenta.id,'currency_id': currency_id.id,
#          'amount_currency':amount_currency,'debit':debito,'credit':credito,
#           })
#          lines = [(0, 0, line)]
#          l.write({'line_ids': lines})
     

    
class Import_detail_journal(models.Model):
    _inherit = 'account.move'    
   # _name = 'import.detail.journal'
    _description = "Importar detalle de diario"

    File_slect = fields.Binary(string="Select Excel File")
    prueba=fields.Char('Report_Name')
    importar_detalle=fields.Boolean('Import detail journal')   
    excel_binary = fields.Binary('Excel file revision')
    file_name = fields.Char('Report_Name', readonly=True)
    allow_differences=fields.Boolean('Allow Differences')  

    def _check_balanced(self):
        if self.importar_detalle == True :
            ''' Assert the move is fully balanced debit = credit.
            An error is raised if it's not the case.
            '''
            moves = self.filtered(lambda move: move.line_ids)
            if not moves:
                return

            # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
            # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
            # It happens as the ORM makes the create with the 'no_recompute' statement.
            self.env['account.move.line'].flush(self.env['account.move.line']._fields)
            self.env['account.move'].flush(['journal_id'])
            self._cr.execute('''
                SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
                FROM account_move_line line
                JOIN account_move move ON move.id = line.move_id
                JOIN account_journal journal ON journal.id = move.journal_id
                JOIN res_company company ON company.id = journal.company_id
                JOIN res_currency currency ON currency.id = company.currency_id
                WHERE line.move_id IN %s
                GROUP BY line.move_id, currency.decimal_places
                HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
            ''', [tuple(self.ids)])

            query_res = self._cr.fetchall()
            if query_res:
                ids = [res[0] for res in query_res]
                sums = [res[1] for res in query_res]
                #raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))

        else:
            ''' Assert the move is fully balanced debit = credit.
            An error is raised if it's not the case.
            '''
            moves = self.filtered(lambda move: move.line_ids)
            if not moves:
                return

            # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
            # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
            # It happens as the ORM makes the create with the 'no_recompute' statement.
            self.env['account.move.line'].flush(self.env['account.move.line']._fields)
            self.env['account.move'].flush(['journal_id'])
            self._cr.execute('''
                SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
                FROM account_move_line line
                JOIN account_move move ON move.id = line.move_id
                JOIN account_journal journal ON journal.id = move.journal_id
                JOIN res_company company ON company.id = journal.company_id
                JOIN res_currency currency ON currency.id = company.currency_id
                WHERE line.move_id IN %s
                GROUP BY line.move_id, currency.decimal_places
                HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
            ''', [tuple(self.ids)])

            query_res = self._cr.fetchall()
            if query_res:
                ids = [res[0] for res in query_res]
                sums = [res[1] for res in query_res]
                raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))




    def import_file(self): 
    
     try:
        fp= tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.File_slect))
        fp.seek(0)
      
        workbook = xlrd.open_workbook(fp.name)
        #sheet = workbook.sheet_by_name("Hoja1")
        sheet = workbook.sheet_by_index(0)   
        #saber cantidad de fils  sheet.nrows
        

     except:
            raise UserError(_("Invalid file!"))



     sum_debi=0
     sum_cred=0
     self.ref=sheet.cell_value(0,0)    
     for i in range(sheet.nrows):
            cuenta=sheet.cell_value(i,0)
            if i >=2 :
                for l in self:
                        id_cuenta = self.env['account.account'].search([('code','=',cuenta)])  
                              
                        debito_rev=sheet.cell_value(i,1)
                        credito_rev=sheet.cell_value(i,2) 

                        debito=0
                        credito=0
                        if   debito_rev:
                           debito=debito_rev  
                        if  credito_rev:   
                           credito =credito_rev 
                        
                        descrip=sheet.cell_value(i,3)                              
                        line = ({'account_id': id_cuenta.id,'debit':debito,'credit':credito,'name':descrip,
                            })
                        lines = [(0, 0, line) ]          
                        l.write({'line_ids': lines})
                        sum_debi+=debito
                        sum_cred+=credito
                        
     
     Total=sum_debi-sum_cred
     if Total!=0 and  self.allow_differences == False :
       for l in self:
         l.line_ids.unlink() 
       raise UserError(_("Do not allow difference between debits and credits"))
       
        
                     

         # line = ({'account_id': id_cuenta.id,'currency_id': currency_id.id,
         #  'amount_currency':amount_currency,'debit':debito,'credit':credito,
         #    })


    def borrar_tabla(self):
        for l in self:
         l.line_ids.unlink()
    
    def revisar_cuenta (self):
        try:
             fp= tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
             fp.write(binascii.a2b_base64(self.File_slect))
             fp.seek(0)
        
             workbook = xlrd.open_workbook(fp.name)
             #sheet = workbook.sheet_by_name("Hoja1")
             sheet = workbook.sheet_by_index(0)   
             #saber cantidad de fils  sheet.nrows
            

        except:
                 raise UserError(_("Invalid file!"))

        
        workbook2 = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        sheet1 = workbook2.add_sheet('Account movement report')     
        sheet1.write(0, 0, _('Accounts'))  

        # fp2 = io.BytesIO()
        # workbook2.save(fp2)
        # excel_file = base64.encodestring(fp2.getvalue())
        # self.excel_binary = excel_file
        # nombre_tabla = "Account Report.xls"
        # self.file_name = nombre_tabla
        # fp2.close() 


        correcto = False
        n=0

        for i in range(sheet.nrows):       
                 if i >=2 :
                     cuenta=sheet.cell_value(i,0)
                     id_cuenta = self.env['account.account'].search([('code','=',cuenta)])
                     if not id_cuenta :
                         n=n+1
                         correcto=True                                       
                         sheet1.write(n, 0, cuenta)
        
        if correcto == True:
         
             fp2 = io.BytesIO()
             workbook2.save(fp2)
             excel_file = base64.encodestring(fp2.getvalue())
             self.excel_binary = excel_file
             nombre_tabla = "Error Accounts.xls"
             self.file_name = nombre_tabla
             fp2.close()

    
            




                              
                  
            
         
