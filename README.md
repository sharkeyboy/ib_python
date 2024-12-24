## Quickstart

1. Clone the repository to your local machine.
2. Install project dependencies by running: `pip install -r requirements.txt`.
3. Copy your private signature and encryption keys into the project.
4. Create a .env file in the project root directory. The .env file should contain the following fields:

  - **CONSUMER_KEY**: The consumer key configured during the onboarding process. This uniquely identifies the project in the IBKR ecosystem.
  - **SIGNATURE_KEY_FP**: The path to the private signature key.
  - **ENCRYPTION_KEY_FP**: The path to the private encryption key.
  - **REALM**: The realm. This is generally set to "limited_poa", however should be set to "test_realm" when using the TESTCONS consumer key.
  - **DH_PRIME**: The hex representation of the Diffie-Hellman prime.
  - **DH_GENERATOR**: The Diffie-Hellman generator value. This is usually 2.


## dhparms/DH_PRIME

Regarding the dhparams, which is needed to be uploaded to IB portal, and is required for the **DH_PRIME** above, see this issue [here](https://github.com/sharkeyboy/ib_python/issues/1), but in brief, creating the dhparams.pem, on my mac anyway, didn't output a file, like I expected, instead the content of that file was output to the console:

`openssl dhparam -outform PEM 2048 -out dhparam_mark.pem`

output:

`Generating DH parameters, 2048 bit long safe prime, generator 2
This is going to take a long time
............................................................................................................................................................................+..............+.+................................................................................................................................+........................
-----BEGIN DH PARAMETERS-----
MIIBCAKCAQEA+md1nRbqgcqfPyqhGzTNQSx8ZaBVA892kRhCMbLysKurOg0uzTHX
gY0+w2vr9+es7N78twOQ1ESBXc+AG1ucxc+KtsBDAz8Aydn+ZDtFb+yIgWw0tEzD
1BniL9lyHCckyRm4SUtCSjkACov7/kAmqRtxgGU8B+Yh5zFK6ZlPQgDesFPszXGD
/KSrSAnEvw1SVS/gpSHMU/QeqW5JHf3RSFs1JX3A1rTej+yHTVRZFYk/rzO4A+Kt
lzNyXB9RYPsTyUpphozTP7Gszzzo3faZSD+2JxryyczXKKuPSlAb18jjyQwHibyf
A6OdtX97e2kgrmFtIPPV8dmoAci0xgj3OwIBAg==
-----END DH PARAMETERS-----
`

I copied the `-----BEGIN ... END DH PARAMETERS-----`:

`-----BEGIN DH PARAMETERS-----
MIIBCAKCAQEA+md1nRbqgcqfPyqhGzTNQSx8ZaBVA892kRhCMbLysKurOg0uzTHX
gY0+w2vr9+es7N78twOQ1ESBXc+AG1ucxc+KtsBDAz8Aydn+ZDtFb+yIgWw0tEzD
1BniL9lyHCckyRm4SUtCSjkACov7/kAmqRtxgGU8B+Yh5zFK6ZlPQgDesFPszXGD
/KSrSAnEvw1SVS/gpSHMU/QeqW5JHf3RSFs1JX3A1rTej+yHTVRZFYk/rzO4A+Kt
lzNyXB9RYPsTyUpphozTP7Gszzzo3faZSD+2JxryyczXKKuPSlAb18jjyQwHibyf
A6OdtX97e2kgrmFtIPPV8dmoAci0xgj3OwIBAg==
-----END DH PARAMETERS-----`

(the line breaks are screwed up), it needs to look like:
<img width="651" alt="image" src="https://github.com/user-attachments/assets/71027188-b0a5-4e3d-b7a5-a00778b90da2" />

 and saved in a file called `dhparams_mark.pem`

to get the **DH_PRIME** I then executed

`openssl asn1parse -in dhparam_mark.pem`

which output

`
    0:d=0  hl=4 l= 264 cons: SEQUENCE          
    4:d=1  hl=4 l= 257 prim: INTEGER           :FA67759D16EA81CA9F3F2AA11B34CD412C7C65A05503CF7691184231B2F2B0ABAB3A0D2ECD31D7818D3EC36BEBF7E7ACECDEFCB70390D444815DCF801B5B9CC5CF8AB6C043033F00C9D9FE643B456FEC88816C34B44CC3D419E22FD9721C2724C919B8494B424A39000A8BFBFE4026A91B7180653C07E621E7314AE9994F4200DEB053ECCD7183FCA4AB4809C4BF0D52552FE0A521CC53F41EA96E491DFDD1485B35257DC0D6B4DE8FEC874D545915893FAF33B803E2AD9733725C1F5160FB13C94A69868CD33FB1ACCF3CE8DDF699483FB6271AF2C9CCD728AB8F4A501BD7C8E3C90C0789BC9F03A39DB57F7B7B6920AE616D20F3D5F1D9A801C8B4C608F73B
  265:d=1  hl=2 l=   1 prim: INTEGER           :02
`

I used the 

`FA67759D16EA81CA9F3F2AA11B34CD412C7C65A05503CF7691184231B2F2B0ABAB3A0D2ECD31D7818D3EC36BEBF7E7ACECDEFCB70390D444815DCF801B5B9CC5CF8AB6C043033F00C9D9FE643B456FEC88816C34B44CC3D419E22FD9721C2724C919B8494B424A39000A8BFBFE4026A91B7180653C07E621E7314AE9994F4200DEB053ECCD7183FCA4AB4809C4BF0D52552FE0A521CC53F41EA96E491DFDD1485B35257DC0D6B4DE8FEC874D545915893FAF33B803E2AD9733725C1F5160FB13C94A69868CD33FB1ACCF3CE8DDF699483FB6271AF2C9CCD728AB8F4A501BD7C8E3C90C0789BC9F03A39DB57F7B7B6920AE616D20F3D5F1D9A801C8B4C608F73B`
for the `DH_PRIME` value in .env.

