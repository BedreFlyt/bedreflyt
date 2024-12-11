BEGIN TRANSACTION;
CREATE TABLE "roomCategory" (
	"catId"	TEXT,
	"roomDescr"	TEXT,
	"catIdModl"	INTEGER
);
INSERT INTO "roomCategory" VALUES('001','Sengepost',1);
INSERT INTO "roomCategory" VALUES('002','Intermediær',2);
INSERT INTO "roomCategory" VALUES('003','Overvåkning',3);
INSERT INTO "roomCategory" VALUES('004','Operasjonsrom',4);

CREATE TABLE "roomDistrib" (
	"roomNr"	INTEGER,
	"roomNrMod"	INTEGER,
	"bedCategory"	INTEGER,
	"capacity"	INTEGER,
	"bathroom"	INTEGER
);
INSERT INTO "roomDistrib" VALUES(3,1,1,2,1);
INSERT INTO "roomDistrib" VALUES(2,0,1,1,1);
INSERT INTO "roomDistrib" VALUES(4,2,1,2,1);
INSERT INTO "roomDistrib" VALUES(19,3,1,3,1);
INSERT INTO "roomDistrib" VALUES(21,4,1,1,0);
INSERT INTO "roomDistrib" VALUES(22,5,1,4,0);
INSERT INTO "roomDistrib" VALUES(36,6,1,4,1);
INSERT INTO "roomDistrib" VALUES(38,7,1,2,1);
INSERT INTO "roomDistrib" VALUES(23,8,2,3,0);
INSERT INTO "roomDistrib" VALUES(28,9,2,2,0);
INSERT INTO "roomDistrib" VALUES(29,10,2,1,1);
INSERT INTO "roomDistrib" VALUES(31,11,2,3,1);
INSERT INTO "roomDistrib" VALUES(6,12,3,3,1);
INSERT INTO "roomDistrib" VALUES(43,13,3,3,0);
INSERT INTO "roomDistrib" VALUES(100,14,4,1,0);
INSERT INTO "roomDistrib" VALUES(200,15,4,1,0);
INSERT INTO "roomDistrib" VALUES(300,16,4,1,0);
COMMIT;
