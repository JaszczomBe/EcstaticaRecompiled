#ifndef E2RECOMP_TEST_POPULATION_H
#define E2RECOMP_TEST_POPULATION_H

#include <stdlib.h>
#include <string.h>

/* Explicit test fixture, never inferred from diagnostic marker labels or the
 * collision flag (doors and stocks also carry that flag). These original global
 * actors are gob3/gob3b in St_gobsc and korc2 in blaksmit. The fixture is scoped
 * to the opening regression routes; new regions need their own audited actors.
 * Normal gameplay does not select this policy. */
static int E2R_TestNoncombatPopulation(void)
{
    const char *profile = getenv("E2R_TEST_POPULATION");
    return profile != NULL && strcmp(profile, "noncombat-opening") == 0;
}

static unsigned E2R_test_suppressed_mask;

static int E2R_TestSuppressActor(int actor_id)
{
    if (!E2R_TestNoncombatPopulation()) return 0;
    unsigned bit = actor_id == 284 ? 1u : actor_id == 293 ? 2u : actor_id == 602 ? 4u : 0u;
    E2R_test_suppressed_mask |= bit;
    return bit != 0;
}

#endif
