BEGIN TRANSACTION;
CREATE TABLE "patient" (
	"patientId"	TEXT,
	"gender"	TEXT,
	"genderModl"	TEXT
);
INSERT INTO "patient" VALUES('einar','male','False');
INSERT INTO "patient" VALUES('rudi','male','False');
INSERT INTO "patient" VALUES('lizeth','female','True');
INSERT INTO "patient" VALUES('laura','female','True');
INSERT INTO "patient" VALUES('riccardo','male','False');
CREATE TABLE "patientStatus" (
	"patientId"	TEXT,
	"infectius"	TEXT,
	"roomNr"	INTEGER
);
INSERT INTO "patientStatus" VALUES('einar','False',0);
INSERT INTO "patientStatus" VALUES('rudi','False',0);
INSERT INTO "patientStatus" VALUES('lizeth','True',0);
INSERT INTO "patientStatus" VALUES('laura','False',0);
INSERT INTO "patientStatus" VALUES('riccardo','True',0);
CREATE TABLE "scenario" (
	"batch"	INTEGER,
	"patientId"	TEXT,
	"treatmentName"	TEXT
);
INSERT INTO "scenario" VALUES(1,'einar','standard');
INSERT INTO "scenario" VALUES(1,'rudi','inter');
INSERT INTO "scenario" VALUES(2,'lizeth','intense1');
INSERT INTO "scenario" VALUES(4,'laura','standard');
INSERT INTO "scenario" VALUES(4,'riccardo','intense2');
CREATE INDEX IF NOT EXISTS scenario_batch ON scenario(batch);

COMMIT;
