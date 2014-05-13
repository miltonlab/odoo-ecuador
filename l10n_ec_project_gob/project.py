# -*- coding: utf-8 -*-
################################################################################
#                
#    l10n_project_gob module for OpenERP, Project Management for Gov in Ecuador
#    Copyright (C) 2014 Gnuthink Cia. Ltda. (<https://github.com/openerp-ecuador/openerp-ecuador>) 
#                
#    This file is a part of l10n_project_gob
#                
#    l10n_project_gob is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the 
#    License, or (at your option) any later version.
#                
#    l10n_project_gob is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#                
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#                
#################################################################################

import logging

from osv import osv, fields


class AnalyticAccount(osv.osv):
    _inherit = 'account.analytic.account'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, '%s - %s' % (elmt.code, elmt.name)))
        return res    

    _columns = {
        'type': fields.selection([('view','Analytic View'),
                                  ('normal','Analytic Account'),
                                  ('contract','Contract or Project'),
                                  ('budget', 'Presupuesto'),
                                  ('template','Template of Contract')],
                                  'Type of Account',
                                  required=True,
                                 help="If you select the View Type, it means you won\'t allow to create journal entries using that account.\n"\
                                  "The type 'Analytic account' stands for usual accounts that you only want to use in accounting.\n"\
                                  "If you select Contract or Project, it offers you the possibility to manage the validity and the invoicing options for this account.\n"\
                                  "The special type 'Template of Contract' allows you to define a template with default data that you can reuse easily."),        
        }


class ProjectProperty(osv.osv):
    """
    Propiedades de proyectos
    """
    _name = 'project.property'
    _description = 'Propiedades de Proyecto'

    _columns = dict(
        name = fields.char('Descripción', size=128),
        project_id = fields.many2one('project.project', string='Proyecto'),
        type_id = fields.many2one('project.type', string='Tipo'),
        )


class ProjectType(osv.osv):
    """
    Tipos de proyectos que definen propiedades por defecto
    """
    _name = 'project.type'
    _description = 'Tipos de Proyectos'
    _order = 'name DESC'

    _columns = dict(
        code = fields.char('Código', size=12, required=True),
        name = fields.char('Tipo de Proyecto', size=64, required=True, select=True),
        properties_ids = fields.one2many('project.property', 'type_id',
                                         string="Propiedades por Tipo de Proyecto"),
        kpi_ids = fields.one2many('project.project.kpi', 'project_type_id', string='Indicadores'),
        )


class ProjectKpi(osv.osv):
    _name = 'project.kpi'

    def _get_complete_formula(self, cr, uid, ids, fields, args, context):
        """
        Metodo que genera el campo que contiene la formula completa
        """
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = ' '.join([obj.numerador, '/', obj.denominador])
        return res    

    _columns = dict(
        name = fields.char('Descripción', size=128, required=True),
        formula = fields.function(_get_complete_formula, method=True, string='Fórmula', type='char'),
        numerador = fields.char('Numerador', size=128, required=True),
        denominador = fields.char('Denominador', size=128, required=True),
        uom_id = fields.many2one('product.uom', 'Unidad de Medida', required=True),
        project_type_id = fields.many2one('project.type', 'Tipo de Proyecto'),
        project_id = fields.many2one('project.project', 'Proyecto', required=True),
        )

    _defaults = dict(
        numerador = '**',
        denominador = '**'
        )    


class ProjectEstrategy(osv.osv):

    _name = 'project.estrategy'
    _description = 'Lista de Estrategias'

    _columns = dict(
        sequence = fields.char('Prioridad', size=16, required=True),
        name = fields.char('Estrategia', size=128, required=True),
        axis_id = fields.many2one('project.axis', 'Eje Estratégico', required=True)
        )


class ProjectAxis(osv.osv):

    _name = 'project.axis'
    _description = 'Ejes Estrategicos'

    _columns = dict(
        name = fields.char('Eje Estratégico', size=64, required=True),
        legal_base = fields.text('Objetivo'),
        )

class ProjectProgram(osv.osv):

    _name = 'project.program'
    _description = 'Buscar Programas'

    def onchange_estrategy(self, cr, uid, ids, estrategy_id):
        """
        Metodo que devuelve el eje segun la estrategia seleccionada
        """
        res = {'value': {'axis_id': ''}}
        if estrategy_id:
            estrat = self.pool.get('project.estrategy').read(cr, uid, estrategy_id, ['axis_id'])
            res['value']['axis_id'] = estrat['axis_id']
        return res
        
    _columns = dict(
        sequence = fields.char('Código', size=32, required=True),
        name = fields.char('Programa', size= 64, required=True),
        estrategy_id = fields.many2one('project.estrategy',
                                  string='Estrategia',
                                  required=True),
        axis_id = fields.related('estrategy_id', 'axis_id', relation='project.axis',
                                 type='many2one', string='Eje Estratégico',
                                 readonly=True, store=True),
        description = fields.text('Descripción'),
        )

class ProjectProject(osv.osv):
    _inherit = 'project.project'
    __logger = logging.getLogger(_inherit)    
    STATES = {'draft':[('readonly',False)]}

    _columns = {
        'department_id': fields.many2one('hr.department',
                                         string='Departamento',
                                         required=True),
        'axis_id': fields.many2one('project.axis',
                                   string='Eje',
                                   required=True,
                                   readonly=True, states=STATES),
        'estrategy_id': fields.many2one('project.estrategy',
                                        string='Estrategia',
                                        required=True,
                                        readonly=True, states=STATES),
        'program_id': fields.many2one('project.program',
                                      string='Programa',
                                      required=True,
                                      readonly=True, states=STATES),
        'background': fields.text('Antecendentes',
                                 required=True,
                                 readonly=True,
                                 states=STATES),
        'justification': fields.text('Justificación',
                                    required=True,
                                    readonly=True, states=STATES),
        'general_objective': fields.text('Objetivo General',
                                        required=True,
                                        readonly=True,
                                        states=STATES),
        'specific_objectives': fields.text('Objetivos Específicos',
                                          required=True,
                                          readonly=True,
                                          states=STATES),
        'type_id': fields.many2one('project.type', 'Tipo de Proyecto',
                                    required=True,
                                    readonly=True,
                                    states=STATES),
        'kpi_ids': fields.one2many('project.kpi', 'project_id',
                                   string='Indicadores'),
        'state': fields.selection([('template', 'Template'),
                                   ('draft','Planificando'),
                                   ('ok','Aprobado'),                                   
                                   ('open','En Ejecución'),
                                   ('cancelled', 'Cancelled'),
                                   ('pending','Pending'),
                                   ('close','Terminado')], 'Status', required=True,),                                   
        }

    _defaults = {
        'state': 'draft'
        }

    def onchange_pnd(self, cr, uid, ids, type_id):
        """
        TODO: ambiguo ?
        """
        res = {'value': {'estrategy_id': False,
                              'program_id': False}}
        if type_id == 'estrat':
            res['value'].pop('estrategy_id')
        return res
            


class ProjectTask(osv.osv):
    _inherit = 'project.task'

    _columns = {
        'budget_ids': fields.one2many('project.budget.plan',
                                      'task_id', 'Presupuesto')
        }


class ProjectBudgetPlan(osv.osv):
    _name = 'project.budget.plan'

    _columns = {
        'account_id': fields.many2one('account.analytic.account', string='Partida',
                                      required=True),
        'name': fields.char('Descripción', size=64, required=True),
        'amount': fields.float('Monto', digits=(8,2)),
        'task_id': fields.many2one('project.task', 'Actividad',
                                   required=True),
        }