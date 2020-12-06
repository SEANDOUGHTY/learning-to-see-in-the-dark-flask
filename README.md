# Learning to See in the Dark Flask App

This repo is a Flask App built upon the [PyTorch Learning to See In the Dark Repository](https://github.com/frankgu968/learning-to-see-in-the-dark-pytorch).

## Setup
1. Clone the repository including the submodules  
`git clone --recurisve` https://github.com/SEANDOUGHTY/learning-to-see-in-the-dark-flask.git

2. Add the pretrained model into /checkpoint/checkpoint.t7

3. Create an AWS bucket for storing input and output images and assign environment variables:
    * `AWS_ACCESS_KEY_ID`
    * `AWS_SECRET_ACCESS_KEY`
    * `AWS_REGION`

4. Build the docker containers  
`docker-compose build`

5. Start the docker container  
`docker-compose up`

## API Calls

After the docker containers are successfully running inference can be performed by using a POST request with the following format:
```
{
    "Bucket": $BUCKETNAME,
    "input-image": $INPUTIMAGE_KEY,
    "output-image": $OUTPUTIMAGE_KEY",
    "ratio": $RATIO
}
```
Ratio is a scaling factor between the original image exposure and the output image exposure.
