import pytest
from system.utils import *
import logging
from indy import IndyError

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')

# THIS TEST SUITE MUST BE RUN AGAINST 7 NODE POOL


@pytest.mark.asyncio
async def test_consensus_restore_after_f_plus_one(pool_handler, wallet_handler,
                                                  get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1 = random_did_and_json()[0]
    did2 = random_did_and_json()[0]
    did3 = random_did_and_json()[0]
    did4 = random_did_and_json()[0]
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    # 7/7 online - can w+r
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    # 5/7 online - can w+r
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[-2:]]
    print(outputs)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    # 4/7 online - can r only
    output = hosts[4].check_output('systemctl stop indy-node')
    print(output)
    time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    with pytest.raises(IndyError):
        await nym_helper(pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    res1 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
    assert res1['result']['seqNo'] is not None
    # 3/7 online - can r only
    output = hosts[3].check_output('systemctl stop indy-node')
    print(output)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    with pytest.raises(IndyError):
        await nym_helper(pool_handler, wallet_handler, trustee_did, did4, None, None, None)
    res2 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did2)
    assert res2['result']['seqNo'] is not None
    # 5/7 online - can w+r
    outputs = [host.check_output('systemctl start indy-node') for host in hosts[3:5]]
    print(outputs)
    time.sleep(60)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did3)
    # 7/7 online - can w+r
    outputs = [host.check_output('systemctl start indy-node') for host in hosts[-2:]]
    print(outputs)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did4)


@pytest.mark.asyncio
async def test_consensus_state_proof_reading(pool_handler, wallet_handler,
                                             get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1 = random_did_and_json()[0]
    did2 = random_did_and_json()[0]
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    time.sleep(15)
    # Stop all except 1
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[1:]]
    print(outputs)
    time.sleep(15)
    res = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
    assert res['result']['seqNo'] is not None
    # Stop the last one
    hosts[0].check_output('systemctl stop indy-node')
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)
    time.sleep(45)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)


@pytest.mark.asyncio
async def test_consensus_n_and_f_changing(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1 = random_did_and_json()[0]
    did2 = random_did_and_json()[0]
    did3 = random_did_and_json()[0]
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    alias, target_did = await demote_random_node(pool_handler, wallet_handler, trustee_did)
    temp_hosts = hosts.copy()
    temp_hosts.pop(int(alias[4:])-1)
    outputs = [host.check_output('systemctl stop indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    with pytest.raises(IndyError):
        await nym_helper(pool_handler, wallet_handler, trustee_did, did1, None, None, None)
    outputs = [host.check_output('systemctl start indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    time.sleep(60)
    await promote_node(pool_handler, wallet_handler, trustee_did, alias, target_did)
    time.sleep(60)
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[-2:]]
    print(outputs)
    res2 = await nym_helper(pool_handler, wallet_handler, trustee_did, did2, None, None, None)
    assert res2['op'] == 'REPLY'
    output = hosts[0].check_output('systemctl stop indy-node')
    print(output)
    time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    with pytest.raises(IndyError):
        await nym_helper(pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)