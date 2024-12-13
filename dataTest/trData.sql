BEGIN TRANSACTION;
CREATE TABLE "taskDependencies" (
  "treatmentName" TEXT,
	"taskName"	TEXT,
	"taskDependency"	TEXT
);
INSERT INTO "taskDependencies" VALUES('standard','surgery1', 'arrival');
INSERT INTO "taskDependencies" VALUES('standard','post-surgery1', 'surgery1');

INSERT INTO "taskDependencies" VALUES('inter','surgery1', 'arrival');
INSERT INTO "taskDependencies" VALUES('inter','post-surgery2', 'surgery1');

INSERT INTO "taskDependencies" VALUES('intense1','analyses', 'arrival');
INSERT INTO "taskDependencies" VALUES('intense1','surgery2', 'analyses');
INSERT INTO "taskDependencies" VALUES('intense1','post-surgery3', 'surgery2');

INSERT INTO "taskDependencies" VALUES('intense2','analyses', 'arrival');
INSERT INTO "taskDependencies" VALUES('intense2','surgery2', 'analyses');
INSERT INTO "taskDependencies" VALUES('intense2','post-surgery3', 'surgery2');
INSERT INTO "taskDependencies" VALUES('intense2','post-surgery4', 'post-surgery3');

CREATE INDEX IF NOT EXISTS taskDependencies_taskName ON taskDependencies(taskName);
CREATE INDEX IF NOT EXISTS taskDependencies_treatmentName ON taskDependencies(treatmentName);

CREATE TABLE "tasks" (
	"name"	TEXT,
	"bedCategory"	INTEGER,
	"durAvg"	INTEGER
);
INSERT INTO "tasks" VALUES('analyses',1,2);
INSERT INTO "tasks" VALUES('arrival',1,1);
INSERT INTO "tasks" VALUES('surgery1',4,1);
INSERT INTO "tasks" VALUES('surgery2',4,1);
INSERT INTO "tasks" VALUES('post-surgery1',2,1);
INSERT INTO "tasks" VALUES('post-surgery2',3,1);
INSERT INTO "tasks" VALUES('post-surgery3',3,2);
INSERT INTO "tasks" VALUES('post-surgery4',2,2);
CREATE INDEX IF NOT EXISTS tasks_name ON tasks(name);

CREATE VIEW treatments (treatmentName, taskName, orderTask) AS
  WITH RECURSIVE tasks(treatmentName, taskName, taskPrio)
  AS (SELECT treatmentName, taskDependency, 0
        FROM taskDependencies base
       WHERE taskDependency NOT IN
             (SELECT taskName
                FROM taskDependencies dep
               WHERE base.treatmentName = dep.treatmentName)
       UNION ALL
      SELECT recur.treatmentName, recur.taskName, tasks.taskPrio + 1
        FROM taskDependencies recur
        JOIN tasks
            ON recur.taskDependency = tasks.taskName
            AND recur.treatmentName = tasks.treatmentName
       ORDER BY 1, 3)
  SELECT *
    FROM tasks;

COMMIT;
