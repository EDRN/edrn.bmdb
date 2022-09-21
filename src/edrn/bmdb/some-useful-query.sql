organ_data
| id                   | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| biomarker_id         | int(10) unsigned | NO   | MUL | NULL    |                |
| organ_id             | int(10) unsigned | NO   | MUL | NULL    |                |
| description          | text             | NO   |     | NULL    |                |
| performance_comment  | text             | NO   |     | NULL    |                |
| sensitivity_min      | int(11)          | NO   |     | NULL    |                |
| sensitivity_max      | int(11)          | NO   |     | NULL    |                |
| sensitivity_comment  | text             | NO   |     | NULL    |                |
| specificity_min      | int(11)          | NO   |     | NULL    |                |
| specificity_max      | int(11)          | NO   |     | NULL    |                |
| specificity_comment  | varchar(200)     | NO   |     | NULL    |                |
| npv_min              | int(11)          | NO   |     | NULL    |                |
| npv_max              | int(11)          | NO   |     | NULL    |                |
| npv_comment          | varchar(200)     | NO   |     | NULL    |                |
| ppv_min              | int(11)          | NO   |     | NULL    |                |
| ppv_max              | int(11)          | NO   |     | NULL    |                |
| ppv_comment          | varchar(200)     | NO   |     | NULL    |                |
| phase                | varchar(40)      | NO   |     | NULL    |                |
| qastate              | varchar(40)      | NO   |     | NULL    |                |
| clinical_translation | varchar(4)       | NO   |     | None    |                |

biomarkers
| id           | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| name         | varchar(200)     | NO   |     | NULL    |                |
| shortName    | varchar(20)      | NO   |     | NULL    |                |
| created      | datetime         | NO   |     | NULL    |                |
| modified     | datetime         | NO   |     | NULL    |                |
| description  | text             | NO   |     | NULL    |                |
| qastate      | varchar(25)      | NO   |     | NULL    |                |
| phase        | varchar(25)      | NO   |     | NULL    |                |
| security     | varchar(25)      | NO   |     | NULL    |                |
| type         | varchar(25)      | NO   |     | NULL    |                |
| isPanel      | int(10) unsigned | NO   |     | 0       |                |
| panelID      | int(10) unsigned | NO   |     | NULL    |                |
| curatorNotes | text             | NO   |     | NULL    |                |

organs
| id    | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| name  | varchar(20)      | NO   |     | NULL    |                |

SELECT
    biomarkers.id, biomarkers.name, organs.name
FROM
    organ_data, biomarkers, organs
WHERE
    organ_data.phase = '' AND
    organ_data.biomarker_id = biomarkers.id AND
    organ_data.organ_id = organs.id
;

