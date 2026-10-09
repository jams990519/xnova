import dataclasses

import pytest

from conftest import give, research
from xnova_bot.db import MOON, PLANET
from xnova_bot.game import GameError
from xnova_bot.texts import ATTACK, COLONIZE, DEPLOY, EXPEDITION, RECYCLE, SPY, TRANSPORT

HOUR = 3600


def new_player(game, pid, name):
    player, planet = game.register(pid, pid, name)
    return player, planet


def test_register_places_home_planet(game):
    player, planet = new_player(game, 1, "Ana")
    assert planet.base_fields == 163
    assert 4 <= planet.position <= 12
    assert (planet.metal, planet.crystal) == (500, 500)
    with pytest.raises(GameError):
        game.register(2, 2, "ana")  # names are unique, case-insensitive
    with pytest.raises(GameError):
        game.register(3, 3, "x")


def test_neighbours_share_a_system(game):
    planets = [new_player(game, i, f"Jugador{i}")[1] for i in range(1, 5)]
    assert {(p.galaxy, p.system) for p in planets[:3]} == {(1, 1)}
    assert (planets[3].galaxy, planets[3].system) == (1, 2)


def test_resources_accumulate(game, clock):
    _, planet = new_player(game, 1, "Ana")
    clock.advance(HOUR)
    _, planet = game.view_planet(1)
    assert planet.metal == pytest.approx(520)  # 20 free metal per hour
    assert planet.crystal == pytest.approx(510)


def test_build_and_finish(game, clock):
    _, planet = new_player(game, 1, "Ana")
    game.start_build(1, planet.id, 1)
    with pytest.raises(GameError):
        game.start_build(1, planet.id, 2)  # one at a time
    planet = game.db.get_planet(planet.id)
    assert planet.metal == pytest.approx(440)
    clock.advance(HOUR)
    notices = game.tick()
    assert game.db.get_planet(planet.id).level(1) == 1
    assert any("Mina de metal" in n.text for n in notices)


def test_cancel_build_refunds(game):
    _, planet = new_player(game, 1, "Ana")
    game.start_build(1, planet.id, 1)
    game.cancel_build(1, planet.id)
    assert game.db.get_planet(planet.id).metal == pytest.approx(500)


def test_requirements_block(game):
    _, planet = new_player(game, 1, "Ana")
    give(game, planet.id, 10**6, 10**6, 10**6)
    with pytest.raises(GameError):
        game.start_build(1, planet.id, 21)  # shipyard needs robotics 2
    with pytest.raises(GameError):
        game.start_research(1, planet.id, 113)  # no lab


def test_research(game, clock):
    _, planet = new_player(game, 1, "Ana")
    give(game, planet.id, 10_000, 10_000, 10_000, buildings={31: 1})
    game.start_research(1, planet.id, 113)
    clock.advance(10 * HOUR)
    game.tick()
    assert game.db.get_player(1).tech(113) == 1


def test_shipyard_builds_over_time(game, clock):
    _, planet = new_player(game, 1, "Ana")
    give(game, planet.id, 100_000, 100_000, 0, buildings={21: 2})
    research(game, 1, t115=1)
    planet, count = game.order_units(1, planet.id, 204, 5)
    assert count == 5
    unit = planet.shipyard[0]["unit"]
    clock.advance(unit * 2.5)
    _, planet = game.view_planet(1)
    assert planet.ships.get(204) == 2
    clock.advance(unit * 3)
    _, planet = game.view_planet(1)
    assert planet.ships.get(204) == 5
    assert planet.shipyard == []


def setup_two(game):
    _, a = new_player(game, 1, "Ana")
    _, b = new_player(game, 2, "Beto")
    research(game, 1, t115=6, t106=2, t117=3, t108=10)
    research(game, 2, t115=6)
    return a, b


def test_spy_and_attack_and_recycle(game, clock):
    a, b = setup_two(game)
    give(game, a.id, 0, 0, 100_000, ships={210: 3, 203: 10, 204: 50, 209: 5})
    give(game, b.id, 50_000, 30_000, 10_000, defense={401: 5})
    fleet, _ = game.send_fleet(1, a.id, {210: 3}, b.coords, PLANET, SPY, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    notices = game.tick()
    spy_reports = [n for n in notices if n.player_id == 1 and "Espionaje" in n.text]
    assert spy_reports and any(n.player_id == 2 and "espió" in n.text for n in notices)

    fleet, notices = game.send_fleet(1, a.id, {204: 50, 203: 10}, b.coords, PLANET, ATTACK, 100)
    assert any(n.player_id == 2 and "Ataque en camino" in n.text for n in notices)
    clock.advance(fleet.arrive - clock.t + 1)
    notices = game.tick()
    battle = [n for n in notices if "Batalla" in n.text]
    assert len(battle) == 2
    fleet = game.db.get_fleet(fleet.id)
    assert fleet and fleet.state == "back"
    assert fleet.metal > 0 and fleet.crystal > 0
    target = game.db.get_planet(b.id)
    assert target.metal < 50_000
    clock.advance(fleet.return_at - clock.t + 1)
    game.tick()
    home = game.db.get_planet(a.id)
    assert home.ships.get(203) == 10
    assert home.metal > 0
    assert game.db.get_player(1).xp_raid == 1


def test_noob_protection_and_bash_limit(game, clock):
    game.s = dataclasses.replace(game.s, noob_points_limit=50_000)
    a, b = setup_two(game)
    game.update_ranking()
    with game.db.conn:
        p1, p2 = game.db.get_player(1), game.db.get_player(2)
        p1.points, p2.points = 1000, 10
        game.db.save_player(p1)
        game.db.save_player(p2)
    give(game, a.id, 0, 0, 100_000, ships={204: 10})
    with pytest.raises(GameError, match="novato"):
        game.send_fleet(1, a.id, {204: 1}, b.coords, PLANET, ATTACK, 100)
    with game.db.conn:
        p2 = game.db.get_player(2)
        p2.points = 900
        game.db.save_player(p2)
    for _ in range(6):
        game.send_fleet(1, a.id, {204: 1}, b.coords, PLANET, ATTACK, 100)
    with pytest.raises(GameError):
        game.send_fleet(1, a.id, {204: 1}, b.coords, PLANET, ATTACK, 100)


def test_transport_deploy_colonize_expedition(game, clock):
    a, b = setup_two(game)
    research(game, 1, t124=1)
    give(game, a.id, 100_000, 100_000, 200_000, ships={202: 10, 208: 1, 203: 5})
    # transport to another player
    fleet, _ = game.send_fleet(1, a.id, {202: 2}, b.coords, PLANET, TRANSPORT, 100, (1000, 500, 0))
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    assert game.db.get_planet(b.id).metal >= 1000
    # colonize a free slot
    free = next(p for p in range(1, 16) if not game.db.planet_at(a.galaxy, a.system, p))
    fleet, _ = game.send_fleet(1, a.id, {208: 1, 202: 1}, (a.galaxy, a.system, free), PLANET, COLONIZE, 100,
                               (500, 500, 0))
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    colony = game.db.planet_at(a.galaxy, a.system, free)
    assert colony and colony.owner_id == 1 and colony.metal == 500
    # deploy to the colony
    fleet, _ = game.send_fleet(1, a.id, {202: 2}, colony.coords, PLANET, DEPLOY, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    assert game.db.get_planet(colony.id).ships.get(202) == 2  # the escort of the colony ship went home
    # expedition to position 16
    fleet, _ = game.send_fleet(1, a.id, {203: 5}, (a.galaxy, a.system, 16), PLANET, EXPEDITION, 100)
    clock.advance(fleet.return_at - clock.t + 1)
    notices = game.tick()
    assert any("Expedición" in n.text for n in notices)


def test_recycle_debris(game, clock):
    a, b = setup_two(game)
    research(game, 1, t110=2)
    give(game, a.id, 0, 0, 100_000, ships={209: 2})
    with game.db.conn:
        game.db.set_debris(*b.coords, 30_000, 20_000)
    fleet, _ = game.send_fleet(1, a.id, {209: 2}, b.coords, PLANET, RECYCLE, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    fleet = game.db.get_fleet(fleet.id)
    assert fleet.metal + fleet.crystal == 40_000
    assert sum(game.db.get_debris(*b.coords)) == 10_000


def test_moon_can_appear(game, clock):
    a, b = setup_two(game)
    research(game, 1, t109=10, t110=10, t111=10)
    give(game, a.id, 0, 0, 10**7, ships={215: 300})
    give(game, b.id, defense={}, ships={207: 200})
    game.rng.seed(1)
    fleet, _ = game.send_fleet(1, a.id, {215: 300}, b.coords, PLANET, ATTACK, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    notices = game.tick()
    debris = game.db.get_debris(*b.coords)
    assert sum(debris) > 2_000_000  # 30 % of the destroyed battleships
    assert any("Probabilidad de luna: 20 %" in n.text for n in notices)


def test_vacation(game, clock):
    a, b = setup_two(game)
    game.set_vacation(2, True)
    give(game, a.id, 0, 0, 10_000, ships={204: 1})
    with pytest.raises(GameError, match="vacaciones"):
        game.send_fleet(1, a.id, {204: 1}, b.coords, PLANET, ATTACK, 100)
    with pytest.raises(GameError):
        game.set_vacation(2, False)  # minimum 48 h
    before = game.db.get_planet(b.id).metal
    clock.advance(49 * HOUR)
    game.set_vacation(2, False)
    _, planet = game.view_planet(2)
    assert planet.metal == pytest.approx(before)  # no production while away


def test_alliances(game):
    new_player(game, 1, "Ana")
    new_player(game, 2, "Beto")
    alliance = game.create_alliance(1, "NOVA", "Nova Imperio")
    _, notices = game.join_alliance(2, alliance["invite_code"])
    assert notices[0].player_id == 1
    assert game.alliance_broadcast(2, "hola")[0].player_id == 1
    game.leave_alliance(1)
    assert game.db.get_player(2).alliance_rank == "leader"
    game.leave_alliance(2)
    assert game.db.get_alliance(alliance["id"]) is None


def test_officers(game, clock):
    new_player(game, 1, "Ana")
    with pytest.raises(GameError):
        game.hire_officer(1, 601)
    with game.db.conn:
        p = game.db.get_player(1)
        p.xp_raid = 10
        notices = []
        game._level_up(p, notices)
        game.db.save_player(p)
    assert notices and game.db.get_player(1).officer_points == 1
    game.hire_officer(1, 601)
    assert game.db.get_player(1).officer(601) == 1
    with pytest.raises(GameError):
        game.hire_officer(1, 603)  # no points left and needs Geologist 5


def test_ranking(game, clock):
    _, a = new_player(game, 1, "Ana")
    new_player(game, 2, "Beto")
    give(game, a.id, buildings={1: 10})
    game.update_ranking()
    assert game.db.get_player(1).rank == 1
    assert game.db.get_player(1).points > game.db.get_player(2).points


def test_recall(game, clock):
    a, b = setup_two(game)
    give(game, a.id, 0, 0, 10_000, ships={202: 1})
    fleet, _ = game.send_fleet(1, a.id, {202: 1}, b.coords, PLANET, TRANSPORT, 100)
    clock.advance(60)
    fleet = game.recall_fleet(1, fleet.id)
    assert fleet.state == "back" and fleet.return_at == pytest.approx(clock.t + 60)
    clock.advance(61)
    game.tick()
    assert game.db.get_planet(a.id).ships.get(202) == 1


def test_quick_raid(game, clock):
    a, b = setup_two(game)
    give(game, a.id, 0, 0, 100_000, ships={210: 2, 203: 10, 202: 10})
    give(game, b.id, 100_000, 60_000, 20_000)
    fleet, _ = game.send_fleet(1, a.id, {210: 2}, b.coords, PLANET, SPY, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    report = game.db.reports_of(1)[0]
    raid, _ = game.quick_raid(1, report["id"])
    assert raid.mission == ATTACK and set(raid.ships) <= {202, 203}
    clock.advance(raid.arrive - clock.t + 1)
    game.tick()
    raid = game.db.get_fleet(raid.id)
    assert raid.metal + raid.crystal + raid.deuterium == pytest.approx(90_000, rel=0.02)


def test_moon_buildings(game, clock):
    _, a = new_player(game, 1, "Ana")
    with game.db.conn:
        moon = game.db.get_planet(a.id)
        moon.id, moon.kind, moon.name, moon.base_fields, moon.buildings = 0, MOON, "Luna", 1, {}
        game.db.insert_planet(moon)
    give(game, moon.id, 100_000, 100_000, 100_000)
    with pytest.raises(GameError):
        game.start_build(1, moon.id, 1)  # no mines on moons
    game.start_build(1, moon.id, 41)
    clock.advance(25 * HOUR)
    game.tick()
    used, total = game.fields(game.db.get_planet(moon.id))
    assert (used, total) == (1, 4)


def test_quick_raid_refuses_defended_planets(game, clock):
    a, b = setup_two(game)
    give(game, a.id, 0, 0, 100_000, ships={210: 2, 203: 10})
    give(game, b.id, 100_000, 60_000, 20_000, defense={401: 3})
    fleet, _ = game.send_fleet(1, a.id, {210: 2}, b.coords, PLANET, SPY, 100)
    clock.advance(fleet.arrive - clock.t + 1)
    game.tick()
    with pytest.raises(GameError, match="defensas"):
        game.quick_raid(1, game.db.reports_of(1)[0]["id"])
