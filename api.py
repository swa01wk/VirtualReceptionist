from livekit.agents import llm
import enum
from typing import Annotated
import logging
from db_driver import DatabaseDriver

logger = logging.getLogger("hotel-booking")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()


class ReservationDetails(enum.Enum):
    RESERVATION_ID = "reservation_id"
    GUEST_NAME = "guest_name"
    ROOM_TYPE = "room_type"
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"


class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()

        self._reservation_details = {
            ReservationDetails.RESERVATION_ID: "",
            ReservationDetails.GUEST_NAME: "",
            ReservationDetails.ROOM_TYPE: "",
            ReservationDetails.CHECK_IN: "",
            ReservationDetails.CHECK_OUT: "",
        }

    def get_reservation_str(self):
        reservation_str = ""
        for key, value in self._reservation_details.items():
            reservation_str += f"{key.value}: {value}\n"

        return reservation_str

    @llm.ai_callable(description="Lookup a reservation by its ID")
    def lookup_reservation(
        self,
        reservation_id: Annotated[
            str, llm.TypeInfo(description="The reservation ID to lookup")
        ],
    ):
        logger.info("Lookup reservation - ID: %s", reservation_id)

        result = DB.get_reservation_by_id(reservation_id)
        if result is None:
            return "Reservation not found"

        self._reservation_details = {
            ReservationDetails.RESERVATION_ID: result.reservation_id,
            ReservationDetails.GUEST_NAME: result.guest_name,
            ReservationDetails.ROOM_TYPE: result.room_type,
            ReservationDetails.CHECK_IN: result.check_in,
            ReservationDetails.CHECK_OUT: result.check_out,
        }

        return f"Reservation details:\n{self.get_reservation_str()}"

    @llm.ai_callable(description="Get details of the current reservation")
    def get_reservation_details(self):
        logger.info("Get reservation details")
        return f"Reservation details:\n{self.get_reservation_str()}"

    @llm.ai_callable(description="Create a new reservation")
    def create_reservation(
        self,
        reservation_id: Annotated[str, llm.TypeInfo(description="The reservation ID")],
        guest_name: Annotated[str, llm.TypeInfo(description="The guest's name")],
        room_type: Annotated[str, llm.TypeInfo(description="The type of room booked")],
        check_in: Annotated[
            str, llm.TypeInfo(description="Check-in date in the format (YYYY-MM-DD)")
        ],
        check_out: Annotated[
            str, llm.TypeInfo(description="Check-out date in the format (YYYY-MM-DD)")
        ],
    ):
        logger.info(
            "Create reservation - ID: %s, Guest: %s, Room: %s, Check-in: %s, Check-out: %s",
            reservation_id,
            guest_name,
            room_type,
            check_in,
            check_out,
        )

        result = DB.create_reservation(
            reservation_id, guest_name, room_type, check_in, check_out
        )
        if result is None:
            return "Failed to create reservation"

        self._reservation_details = {
            ReservationDetails.RESERVATION_ID: result.reservation_id,
            ReservationDetails.GUEST_NAME: result.guest_name,
            ReservationDetails.ROOM_TYPE: result.room_type,
            ReservationDetails.CHECK_IN: result.check_in,
            ReservationDetails.CHECK_OUT: result.check_out,
        }

        return "Reservation created successfully!"

    def has_reservation(self):
        return self._reservation_details[ReservationDetails.RESERVATION_ID] != ""
