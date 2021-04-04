from datetime import datetime

from bson import ObjectId

from core.motor_client import SingletonClient


DEFAULT_STATUS = 'waiting'


db = SingletonClient.get_data_base().Payments


async def create_payment(
        payer: ObjectId,
        real_payer: ObjectId,
        amount: int,
        contribution: ObjectId,
        screen_id: str,
        payment_platform: str,
        payment_date: datetime,
) -> ObjectId:
    return await db.insert_one({
        'payer': payer,
        'real_payer': real_payer,
        'amount': amount,
        'contribution': contribution,
        'payment_platform': payment_platform,
        'screen_id': screen_id,
        'status': DEFAULT_STATUS,
        'created_date': datetime.utcnow(),
        'payment_date': payment_date
    })
