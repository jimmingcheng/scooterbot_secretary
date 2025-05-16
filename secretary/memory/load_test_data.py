from secretary.memory.fact import Fact


def run():
    Fact(
        user_id='jimming',
        content='''
Quantity	Brand	Item	Description	Ship Location	Scheduled Del	Amount
1	Sub-Zero Refrigerators	CL4250UFDIDSP
Built-In French Door Refigerator	42" CLASSIC FD REFRIG/FREEZER	a. Product Distribution Center		$14,505.00
1	Frigidaire Parts	5308815072
Delivery & Install Parts	6' BRAIDED STAINLESS STEEL IM	a. Product Distribution Center		$24.95
1	Thermador	POD301RW
Single Wall Electric Oven	PRO SGL OVEN, 30", SS, DELUXE, RIGHT SIDE-OPENING	a. Product Distribution Center		$6,049.00
1	Thermador	CIT36YWBB
Induction Cooktop	36" MASTERPIECE FREEDOM INDUCTION COOKTOP, DARK GR	a. Product Distribution Center		$6,099.00
1	Thermador	VCIN36GWSPRO
Vent Insert	36IN INSERT HOOD PROMO	a. Product Distribution Center		$0.01
1	Thermador	VTI2FZ
Vent Blower	1000 CFM IN-LINE BLOWER	a. Product Distribution Center		$899.00
1	EPIC	5YREFBEL20T
Refrigerator Warranty	5 Year Refrigeration Warranty	a. Product Distribution Center		$0.01
1	EPIC	5YAPPBEL10T
Major Appliance Warranty	5 Yr Major Appliance Warranty	a. Product Distribution Center		$0.01
1	EPIC	5YAPPBEL10T
Major Appliance Warranty	5 Yr Major Appliance Warranty	a. Product Distribution Center		$0.01
1	EPIC	5YAPPBEL600
Major Appliance Warranty	5 Yr Major Appliance Warranty	a. Product Distribution Center		$0.01
 	Subtotal	$27,577.00
 	Tax Total (%)	$2,275.10
 	Discount Total	
 	Total	$29,852.10
''',  # noqa
        tags=['house remodel']
    ).upsert()


if __name__ == "__main__":
    run()
